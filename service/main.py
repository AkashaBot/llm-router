# LLM Router Service - Phase 3: Routing LLM-based avec fallback
"""
Routing intelligent avec 3 modes:
- ollama: Utilise un modèle local via Ollama
- api: Utilise une API légère (OpenRouter)
- hybrid: Ollama avec fallback API
- keywords: Mode Phase 2 (fallback ultime)
"""
import os
import re
import time
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import httpx
from dotenv import load_dotenv
from collections import defaultdict
import threading
import asyncio

load_dotenv()

app = FastAPI(title="LLM Router", version="0.3.0")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body}
    )

# =============================================================================
# CONFIGURATION
# =============================================================================

# OpenRouter (provider cible pour les vrais appels LLM)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "z-ai/glm-5")

# Routing mode: "ollama" | "api" | "hybrid" | "keywords"
ROUTING_MODE = os.getenv("ROUTING_MODE", "hybrid")

# Ollama config (pour routing LLM)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://192.168.1.168:11434")
OLLAMA_ROUTER_MODEL = os.getenv("OLLAMA_ROUTER_MODEL", "qwen2.5:0.5b")

# API config (pour routing LLM fallback)
ROUTER_API_MODEL = os.getenv("ROUTER_API_MODEL", "qwen/qwen-2.5-0.5b")

# Modèles par catégorie (Phase 2 - fallback)
MODEL_MAPPINGS = {
    "tools": ["openrouter/aurora-alpha", "moonshotai/kimi-k2.5", "z-ai/glm-5"],
    "code": ["z-ai/glm-5", "openrouter/aurora-alpha", "openai/gpt-4o-mini"],
    "reasoning": ["openrouter/aurora-alpha", "z-ai/glm-5", "moonshotai/kimi-k2.5"],
    "conversation": ["z-ai/glm-5", "openai/gpt-4o-mini", "openrouter/aurora-alpha"]
}

# Keywords pour fallback
KEYWORDS = {
    "code": ["code", "python", "javascript", "function", "class", "def ", "import ", "bug", "debug", "error", "refactor", "api", "http", "json", "sql", "file", "script", "terminal", "git", "commit", "push", "pull", "react", "vue", "node", "typescript", "java", "c++", "rust", "go", "write code", "create function", "fix ", "solve"],
    "reasoning": ["why", "how", "explain", "analyze", "think", "reason", "prove", "math", "calculate", "solution", "logic", "problem", "determine", "compare", "differentiate", "evaluate", "assess", "complex", "research", "study", "understand", "concept", "theory"],
    "conversation": ["hello", "hi", "hey", "thanks", "thank you", "please", "sorry", "yes", "no", "ok", "okay", "sure", "what", "who", "when", "where", "weather", "news", "info", "help"]
}

SHORT_CONTINUATION = [r"^ok$", r"^okay$", r"^yes$", r"^no$", r"^thanks?$", r"^please$", r"^sure$", r"^right$", r"^got it$", r"^cool$", r"^nice$", r"^[a-zA-Z]{1,3}$"]

# Session state
current_model_per_session: Dict[str, str] = {}

# =============================================================================
# METRICS
# =============================================================================

metrics_lock = threading.Lock()
metrics = {
    "requests_total": 0,
    "requests_success": 0,
    "requests_failed": 0,
    "model_usage": defaultdict(int),
    "category_usage": defaultdict(int),
    "routing_mode_usage": defaultdict(int),
    "total_latency_ms": 0,
    "recent_requests": []
}

def track_request(category: str, model: str, latency_ms: float, success: bool, 
                  routing_mode: str = "keywords", error: str = None):
    with metrics_lock:
        metrics["requests_total"] += 1
        if success:
            metrics["requests_success"] += 1
        else:
            metrics["requests_failed"] += 1
        metrics["model_usage"][model] += 1
        metrics["category_usage"][category] += 1
        metrics["routing_mode_usage"][routing_mode] += 1
        metrics["total_latency_ms"] += latency_ms
        
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "category": category,
            "model": model,
            "latency_ms": round(latency_ms, 2),
            "success": success,
            "routing_mode": routing_mode
        }
        if error:
            entry["error"] = error
        metrics["recent_requests"].append(entry)
        if len(metrics["recent_requests"]) > 100:
            metrics["recent_requests"] = metrics["recent_requests"][-100:]

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class Message(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[List[str]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    user: Optional[str] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Any] = None
    
    class Config:
        extra = "ignore"  # Ignore extra fields from OpenClaw

# =============================================================================
# ROUTING LOGIC
# =============================================================================

ROUTER_PROMPT = """Tu es un routeur de modèles LLM. Analyse la requête et choisis la meilleure catégorie.

Réponds UNIQUEMENT avec un mot: code, reasoning, conversation, ou tools

Règles:
- tools: si la requête nécessite des appels de fonction/outils
- code: pour écrire, corriger, expliquer du code
- reasoning: pour analyser, raisonner, expliquer un concept complexe
- conversation: pour les discussions simples, questions rapides

Requête: {message}

Catégorie:"""

def detect_category_keywords(message: str) -> str:
    """Phase 2: Détection par keywords"""
    message_lower = message.lower()
    for keyword in KEYWORDS["code"]:
        if keyword in message_lower:
            return "code"
    for keyword in KEYWORDS["reasoning"]:
        if keyword in message_lower:
            return "reasoning"
    for keyword in KEYWORDS["conversation"]:
        if keyword in message_lower:
            return "conversation"
    return "conversation"

def is_continuation(message: str) -> bool:
    msg = message.strip().lower()
    for pattern in SHORT_CONTINUATION:
        if re.match(pattern, msg, re.IGNORECASE):
            return True
    return False

async def route_with_ollama(message: str) -> Tuple[str, str]:
    """Route via Ollama (LLM local)"""
    prompt = ROUTER_PROMPT.format(message=message[:500])
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_ROUTER_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 10
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            category = result.get("response", "").strip().lower()
            
            # Valider la catégorie
            valid = ["code", "reasoning", "conversation", "tools"]
            if category in valid:
                return category, "ollama"
            return "conversation", "ollama"
        except Exception as e:
            print(f"Ollama routing failed: {e}")
            raise

async def route_with_api(message: str) -> Tuple[str, str]:
    """Route via API (OpenRouter)"""
    prompt = ROUTER_PROMPT.format(message=message[:500])
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": ROUTER_API_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 10,
                    "temperature": 0.1
                }
            )
            response.raise_for_status()
            result = response.json()
            category = result["choices"][0]["message"]["content"].strip().lower()
            
            valid = ["code", "reasoning", "conversation", "tools"]
            if category in valid:
                return category, "api"
            return "conversation", "api"
        except Exception as e:
            print(f"API routing failed: {e}")
            raise

async def route_message(messages: List[Dict], session_id: str, has_tools: bool = False) -> Tuple[str, str]:
    """
    Route le message et retourne (category, routing_mode)
    """
    if not messages:
        return "conversation", "none"
    
    # Si tools présents, catégorie tools
    if has_tools:
        return "tools", "direct"
    
    # Dernier message utilisateur
    last_user_msg = None
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "")
            break
    
    if not last_user_msg:
        return "conversation", "none"
    
    # Continuation courte
    if is_continuation(last_user_msg) and session_id in current_model_per_session:
        return "conversation", "continuation"
    
    # Phase 3: Routing LLM
    if ROUTING_MODE in ["ollama", "hybrid"]:
        try:
            category, mode = await route_with_ollama(last_user_msg)
            if ROUTING_MODE == "ollama":
                return category, mode
            # hybrid: on garde le résultat mais on a le fallback API si besoin
            return category, mode
        except:
            pass
    
    if ROUTING_MODE in ["api", "hybrid"]:
        try:
            category, mode = await route_with_api(last_user_msg)
            return category, mode
        except:
            pass
    
    # Fallback: keywords (Phase 2)
    category = detect_category_keywords(last_user_msg)
    return category, "keywords"

# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "llm-router",
        "version": "0.3.0",
        "routing_mode": ROUTING_MODE,
        "ollama_url": OLLAMA_BASE_URL,
        "ollama_model": OLLAMA_ROUTER_MODEL
    }

@app.get("/metrics")
async def get_metrics():
    with metrics_lock:
        avg_latency = (
            metrics["total_latency_ms"] / metrics["requests_total"]
            if metrics["requests_total"] > 0 else 0
        )
        return {
            "requests": {
                "total": metrics["requests_total"],
                "success": metrics["requests_success"],
                "failed": metrics["requests_failed"]
            },
            "avg_latency_ms": round(avg_latency, 2),
            "model_distribution": dict(metrics["model_usage"]),
            "category_distribution": dict(metrics["category_usage"]),
            "routing_mode_distribution": dict(metrics["routing_mode_usage"]),
            "config": {
                "routing_mode": ROUTING_MODE,
                "ollama_url": OLLAMA_BASE_URL,
                "ollama_model": OLLAMA_ROUTER_MODEL
            },
            "recent_requests": metrics["recent_requests"][-10:]
        }

@app.get("/config")
async def get_config():
    return {
        "routing_mode": ROUTING_MODE,
        "ollama": {
            "base_url": OLLAMA_BASE_URL,
            "model": OLLAMA_ROUTER_MODEL
        },
        "api": {
            "model": ROUTER_API_MODEL
        },
        "model_mappings": MODEL_MAPPINGS
    }

@app.post("/v1/chat/completions")
@app.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured")
    
    print(f"Received request: model={request.model}, messages={len(request.messages)}, tools={len(request.tools) if request.tools else 0}")
    
    start_time = time.time()
    
    # Détection catégorie
    session_id = request.user or "default_session"
    has_tools = request.tools is not None and len(request.tools) > 0
    
    category, routing_mode = await route_message(
        [msg.model_dump() for msg in request.messages],
        session_id,
        has_tools
    )
    
    models_to_try = MODEL_MAPPINGS.get(category, MODEL_MAPPINGS["conversation"])
    
    # Try each model
    last_error = None
    last_model_tried = None
    
    for selected_model in models_to_try:
        last_model_tried = selected_model
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3456",
            "X-Title": "LLM Router"
        }
        
        payload = {
            "model": selected_model,
            "messages": [msg.model_dump(exclude_none=True) for msg in request.messages],
            "temperature": request.temperature,
            "top_p": request.top_p,
            "n": request.n,
            "stream": request.stream,
            "stop": request.stop,
            "max_tokens": request.max_tokens,
            "presence_penalty": request.presence_penalty,
            "frequency_penalty": request.frequency_penalty,
            "user": request.user,
            "tools": request.tools,
            "tool_choice": request.tool_choice
        }
        
        payload = {k: v for k, v in payload.items() if v is not None}
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{OPENROUTER_BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                latency_ms = (time.time() - start_time) * 1000
                track_request(category, selected_model, latency_ms, True, routing_mode)
                
                # Update session model
                current_model_per_session[session_id] = selected_model
                
                return response.json()
            except Exception as e:
                last_error = str(e)
                continue
    
    # All failed
    latency_ms = (time.time() - start_time) * 1000
    track_request(category, last_model_tried or "unknown", latency_ms, False, routing_mode, last_error)
    
    raise HTTPException(status_code=500, detail=f"All models failed. Last error: {last_error}")

@app.on_event("startup")
async def startup_event():
    print(f"LLM Router v0.3.0 started")
    print(f"Routing mode: {ROUTING_MODE}")
    print(f"Ollama: {OLLAMA_BASE_URL} ({OLLAMA_ROUTER_MODEL})")
