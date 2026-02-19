"""
LLM Router Service - Phase 2: Routing intelligent avec détection de catégorie
"""
import os
import re
import time
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import httpx
from dotenv import load_dotenv
from collections import defaultdict
import threading

load_dotenv()

app = FastAPI(title="LLM Router", version="0.2.1")

# Metrics storage
metrics_lock = threading.Lock()
metrics = {
    "requests_total": 0,
    "requests_success": 0,
    "requests_failed": 0,
    "model_usage": defaultdict(int),
    "category_usage": defaultdict(int),
    "total_latency_ms": 0,
    "recent_requests": []  # Last 100 requests
}

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "openai/gpt-5-nano")

# Modèles par catégorie (Phase 2)
# "tools" = requêtes avec function calling → modèles qui le supportent bien
MODEL_MAPPINGS = {
    "tools": ["openrouter/aurora-alpha", "moonshotai/kimi-k2.5", "z-ai/glm-5"],
    "code": ["z-ai/glm-5", "openrouter/aurora-alpha", "openai/gpt-4o-mini"],
    "reasoning": ["openrouter/aurora-alpha", "z-ai/glm-5", "moonshotai/kimi-k2.5"],
    "conversation": ["z-ai/glm-5", "openai/gpt-4o-mini", "openrouter/aurora-alpha"]
}

# Mots-clés pour détection de catégorie
KEYWORDS = {
    "code": ["code", "python", "javascript", "function", "class", "def ", "import ", "bug", "debug", "error", "refactor", "api", "http", "json", "sql", "file", "script", "terminal", "git", "commit", "push", "pull", "react", "vue", "node", "typescript", "java", "c++", "rust", "go", "write code", "create function", "fix ", "solve"],
    "reasoning": ["why", "how", "explain", "analyze", "think", "reason", "prove", "math", "calculate", "solution", "logic", "problem", "determine", "compare", "differentiate", "evaluate", "assess", "complex", "research", "study", "understand", "concept", "theory"],
    "conversation": ["hello", "hi", "hey", "thanks", "thank you", "please", "sorry", "yes", "no", "ok", "okay", "sure", "what", "who", "when", "where", "天气", "weather", "news", "info", "help"]
}

# Messages courts continuation
SHORT_CONTINUATION = [r"^ok$", r"^okay$", r"^yes$", r"^no$", r"^thanks?$", r"^please$", r"^sure$", r"^right$", r"^got it$", r"^cool$", r"^nice$", r"^[\u4e00-\u9fff]+$", r"^[a-zA-Z]{1,3}$"]

# Store current model per session
current_model_per_session: Dict[str, str] = {}

# Pydantic models
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

def detect_category(message: str) -> str:
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

def route_message(messages: List[Dict], session_id: str, return_category: bool = False) -> str:
    if not messages:
        return DEFAULT_MODEL if not return_category else ("conversation", DEFAULT_MODEL)
    
    last_user_msg = None
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "")
            break
    
    if not last_user_msg:
        return DEFAULT_MODEL if not return_category else ("conversation", DEFAULT_MODEL)
    
    # Phase 2: Détection de continuité
    if is_continuation(last_user_msg) and session_id in current_model_per_session:
        return current_model_per_session[session_id] if not return_category else ("conversation", current_model_per_session[session_id])
    
    # Phase 2: Détection de catégorie
    category = detect_category(last_user_msg)
    model = MODEL_MAPPINGS.get(category, MODEL_MAPPINGS["conversation"])[0]
    current_model_per_session[session_id] = model
    
    return category if return_category else model

def track_request(category: str, model: str, latency_ms: float, success: bool, error: str = None):
    """Track request metrics"""
    with metrics_lock:
        metrics["requests_total"] += 1
        if success:
            metrics["requests_success"] += 1
        else:
            metrics["requests_failed"] += 1
        metrics["model_usage"][model] += 1
        metrics["category_usage"][category] += 1
        metrics["total_latency_ms"] += latency_ms
        
        # Keep last 100 requests
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "category": category,
            "model": model,
            "latency_ms": round(latency_ms, 2),
            "success": success
        }
        if error:
            entry["error"] = error
        metrics["recent_requests"].append(entry)
        if len(metrics["recent_requests"]) > 100:
            metrics["recent_requests"] = metrics["recent_requests"][-100:]

@app.get("/metrics")
async def get_metrics():
    """Get routing metrics"""
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
            "recent_requests": metrics["recent_requests"][-10:]  # Last 10
        }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "llm-router", "version": "0.2.1"}

@app.get("/models")
async def list_models():
    return {"data": [{"id": "router", "object": "model", "created": 1700000000, "owned_by": "local"}]}

# Phase 2 enable/disable flag
PHASE2_ENABLED = True  # Enabled for routing

@app.post("/v1/chat/completions")
@app.post("/chat/completions")  # Alias for OpenClaw compatibility
async def chat_completions(request: ChatCompletionRequest):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured")
    
    start_time = time.time()
    
    # Detect category - tools take priority
    has_tools = request.tools is not None and len(request.tools) > 0
    
    if PHASE2_ENABLED:
        session_id = request.user or "default_session"
        
        # If tools present, use tools category (models that support function calling)
        if has_tools:
            category = "tools"
            models_to_try = MODEL_MAPPINGS["tools"]
        else:
            # First call route_message to update session state and get primary model
            primary_model = route_message([msg.model_dump() for msg in request.messages], session_id)
            # Get category from messages for fallback models
            last_user_msg = ""
            for msg in reversed([msg.model_dump() for msg in request.messages]):
                if msg.get("role") == "user":
                    last_user_msg = msg.get("content", "")
                    break
            category = detect_category(last_user_msg) if last_user_msg else "conversation"
            models_to_try = MODEL_MAPPINGS.get(category, MODEL_MAPPINGS["conversation"])
    else:
        category = "conversation"
        models_to_try = [request.model if request.model else DEFAULT_MODEL]
    
    # Try each model in order (fallback)
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
                
                # Track success
                latency_ms = (time.time() - start_time) * 1000
                track_request(category, selected_model, latency_ms, True)
                
                return response.json()
            except Exception as e:
                last_error = str(e)
                continue  # Try next model
    
    # All models failed - track failure
    latency_ms = (time.time() - start_time) * 1000
    track_request(category, last_model_tried or "unknown", latency_ms, False, last_error)
    
    raise HTTPException(status_code=500, detail=f"All models failed. Last error: {last_error}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3456)
