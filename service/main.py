# LLM Router Service - Phase 3: Routing LLM-based avec fallback
"""
Routing intelligent avec:
- Modes: ollama | api | hybrid | keywords
- Circuit breaker pour les modèles défaillants
- Métriques de coût estimé
- Configuration utilisateur des modèles et catégories
"""
import os
import re
import time
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
import httpx
from dotenv import load_dotenv
from collections import defaultdict
import threading
import asyncio

load_dotenv()

app = FastAPI(title="LLM Router", version="0.4.0")

# =============================================================================
# EXCEPTION HANDLER
# =============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)[:500]}
    )

# =============================================================================
# CONFIGURATION
# =============================================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "z-ai/glm-5")

# Routing mode
ROUTING_MODE = os.getenv("ROUTING_MODE", "hybrid")

# Ollama config
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://192.168.1.168:11434")
OLLAMA_ROUTER_MODEL = os.getenv("OLLAMA_ROUTER_MODEL", "qwen2.5:0.5b")

# API routing fallback
ROUTER_API_MODEL = os.getenv("ROUTER_API_MODEL", "qwen/qwen3-1.7b")

# =============================================================================
# COST ESTIMATES (USD per 1M tokens)
# =============================================================================

MODEL_COSTS = {
    "moonshotai/kimi-k2.5": {"input": 0.10, "output": 0.30},
    "z-ai/glm-5": {"input": 0.05, "output": 0.15},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "openai/gpt-4o": {"input": 2.50, "output": 10.00},
    "qwen/qwen3-1.7b": {"input": 0.01, "output": 0.02},
}

# =============================================================================
# USER CONFIG (loadable from file)
# =============================================================================

CONFIG_FILE = os.getenv("ROUTER_CONFIG_FILE", "router_config.json")

DEFAULT_MODEL_MAPPINGS = {
    "tools": ["moonshotai/kimi-k2.5", "z-ai/glm-5", "openai/gpt-4o-mini"],
    "code": ["z-ai/glm-5", "openai/gpt-4o-mini", "moonshotai/kimi-k2.5"],
    "reasoning": ["moonshotai/kimi-k2.5", "z-ai/glm-5", "openai/gpt-4o-mini"],
    "conversation": ["z-ai/glm-5", "openai/gpt-4o-mini", "moonshotai/kimi-k2.5"]
}

DEFAULT_KEYWORDS = {
    "code": ["code", "python", "javascript", "function", "class", "def ", "import ", "bug", "debug", "error", "refactor", "api", "http", "json", "sql", "file", "script", "terminal", "git", "commit", "push", "pull", "react", "vue", "node", "typescript", "java", "c++", "rust", "go"],
    "reasoning": ["why", "how", "explain", "analyze", "think", "reason", "prove", "math", "calculate", "solution", "logic", "problem", "determine", "compare", "differentiate", "evaluate", "assess", "complex", "research", "study", "understand", "concept", "theory"],
    "conversation": ["hello", "hi", "hey", "thanks", "thank you", "please", "sorry", "yes", "no", "ok", "okay", "sure", "what", "who", "when", "where", "weather", "news", "info", "help"]
}

# Runtime config (can be modified via API)
model_mappings: Dict[str, List[str]] = {}
category_keywords: Dict[str, List[str]] = {}
custom_categories: Dict[str, Dict] = {}  # New user-defined categories

def load_config():
    """Load user config from file"""
    global model_mappings, category_keywords, custom_categories
    
    model_mappings = DEFAULT_MODEL_MAPPINGS.copy()
    category_keywords = DEFAULT_KEYWORDS.copy()
    custom_categories = {}
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                if "model_mappings" in config:
                    model_mappings.update(config["model_mappings"])
                if "keywords" in config:
                    category_keywords.update(config["keywords"])
                if "custom_categories" in config:
                    custom_categories = config["custom_categories"]
                    for cat_name, cat_config in custom_categories.items():
                        if "models" in cat_config:
                            model_mappings[cat_name] = cat_config["models"]
                        if "keywords" in cat_config:
                            category_keywords[cat_name] = cat_config["keywords"]
            print(f"Loaded config from {CONFIG_FILE}")
        except Exception as e:
            print(f"Error loading config: {e}")

def save_config():
    """Save current config to file"""
    config = {
        "model_mappings": model_mappings,
        "keywords": category_keywords,
        "custom_categories": custom_categories
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

load_config()

SHORT_CONTINUATION = [r"^ok$", r"^okay$", r"^yes$", r"^no$", r"^thanks?$", r"^please$", r"^sure$", r"^right$", r"^got it$", r"^cool$", r"^nice$", r"^[a-zA-Z]{1,3}$"]

# Session state
current_model_per_session: Dict[str, str] = {}

# =============================================================================
# CIRCUIT BREAKER
# =============================================================================

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout_sec: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_sec
        self.failures: Dict[str, int] = defaultdict(int)
        self.last_failure: Dict[str, float] = {}
        self.open_circuits: Dict[str, bool] = {}
        self.lock = threading.Lock()
    
    def record_failure(self, model: str):
        with self.lock:
            self.failures[model] += 1
            self.last_failure[model] = time.time()
            if self.failures[model] >= self.failure_threshold:
                self.open_circuits[model] = True
                print(f"Circuit OPEN for {model} (failures: {self.failures[model]})")
    
    def record_success(self, model: str):
        with self.lock:
            self.failures[model] = 0
            self.open_circuits[model] = False
    
    def is_available(self, model: str) -> bool:
        with self.lock:
            if model not in self.open_circuits or not self.open_circuits[model]:
                return True
            
            # Check if recovery timeout has passed
            if model in self.last_failure:
                elapsed = time.time() - self.last_failure[model]
                if elapsed > self.recovery_timeout:
                    print(f"Circuit HALF-OPEN for {model}, testing...")
                    return True
            
            return False
    
    def get_status(self) -> Dict:
        with self.lock:
            return {
                "failures": dict(self.failures),
                "open_circuits": {k: v for k, v in self.open_circuits.items() if v},
                "last_failure": {k: datetime.fromtimestamp(v).isoformat() 
                                 for k, v in self.last_failure.items()}
            }

circuit_breaker = CircuitBreaker()

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
    "total_cost_usd": 0.0,
    "recent_requests": []
}

def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in USD"""
    costs = MODEL_COSTS.get(model, {"input": 0.05, "output": 0.15})
    input_cost = (input_tokens / 1_000_000) * costs["input"]
    output_cost = (output_tokens / 1_000_000) * costs["output"]
    return input_cost + output_cost

def track_request(category: str, model: str, latency_ms: float, success: bool, 
                  routing_mode: str = "keywords", cost_usd: float = 0.0, error: str = None):
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
        metrics["total_cost_usd"] += cost_usd
        
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "category": category,
            "model": model,
            "latency_ms": round(latency_ms, 2),
            "success": success,
            "routing_mode": routing_mode,
            "cost_usd": round(cost_usd, 6)
        }
        if error:
            entry["error"] = error[:200]
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
        extra = "ignore"

class CategoryConfig(BaseModel):
    name: str
    models: List[str]
    keywords: Optional[List[str]] = None
    description: Optional[str] = None

class ModelMappingUpdate(BaseModel):
    category: str
    models: List[str]

# =============================================================================
# ROUTING LOGIC
# =============================================================================

ROUTER_PROMPT = """Tu es un routeur de modèles LLM. Analyse la requête et choisis la meilleure catégorie.

Catégories disponibles:
{categories}

Règles:
- tools: si la requête nécessite des appels de fonction/outils
- code: pour écrire, corriger, expliquer du code
- reasoning: pour analyser, raisonner, expliquer un concept complexe
- conversation: pour les discussions simples, questions rapides
- custom: autres catégories définies par l'utilisateur

Requête: {message}

Catégorie:"""

def detect_category_keywords(message: str) -> str:
    """Détection par keywords"""
    message_lower = message.lower()
    
    # Check custom categories first
    for cat_name, cat_config in custom_categories.items():
        keywords = cat_config.get("keywords", [])
        for keyword in keywords:
            if keyword.lower() in message_lower:
                return cat_name
    
    # Then standard categories
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword.lower() in message_lower:
                return category
    
    return "conversation"

def is_continuation(message: str) -> bool:
    msg = message.strip().lower()
    for pattern in SHORT_CONTINUATION:
        if re.match(pattern, msg, re.IGNORECASE):
            return True
    return False

async def route_with_ollama(message: str) -> Tuple[str, str]:
    """Route via Ollama"""
    categories = list(model_mappings.keys())
    prompt = ROUTER_PROMPT.format(
        categories=", ".join(categories),
        message=message[:500]
    )
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_ROUTER_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 20}
                }
            )
            response.raise_for_status()
            result = response.json()
            category = result.get("response", "").strip().lower()
            
            # Extract first word
            category = category.split()[0] if category.split() else category
            
            if category in model_mappings:
                return category, "ollama"
            return "conversation", "ollama"
        except Exception as e:
            print(f"Ollama routing failed: {e}")
            raise

async def route_with_api(message: str) -> Tuple[str, str]:
    """Route via API"""
    categories = list(model_mappings.keys())
    prompt = ROUTER_PROMPT.format(
        categories=", ".join(categories),
        message=message[:500]
    )
    
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
                    "max_tokens": 20,
                    "temperature": 0.1
                }
            )
            response.raise_for_status()
            result = response.json()
            category = result["choices"][0]["message"]["content"].strip().lower()
            
            category = category.split()[0] if category.split() else category
            
            if category in model_mappings:
                return category, "api"
            return "conversation", "api"
        except Exception as e:
            print(f"API routing failed: {e}")
            raise

async def route_message(messages: List[Dict], session_id: str, has_tools: bool = False) -> Tuple[str, str]:
    """Route le message"""
    if not messages:
        return "conversation", "none"
    
    if has_tools:
        return "tools", "direct"
    
    last_user_msg = None
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "")
            break
    
    if not last_user_msg:
        return "conversation", "none"
    
    if is_continuation(last_user_msg) and session_id in current_model_per_session:
        return "conversation", "continuation"
    
    if ROUTING_MODE in ["ollama", "hybrid"]:
        try:
            category, mode = await route_with_ollama(last_user_msg)
            if ROUTING_MODE == "ollama":
                return category, mode
            return category, mode
        except:
            pass
    
    if ROUTING_MODE in ["api", "hybrid"]:
        try:
            category, mode = await route_with_api(last_user_msg)
            return category, mode
        except:
            pass
    
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
        "version": "0.4.0",
        "routing_mode": ROUTING_MODE,
        "ollama_url": OLLAMA_BASE_URL,
        "ollama_model": OLLAMA_ROUTER_MODEL,
        "categories": list(model_mappings.keys())
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
            "total_cost_usd": round(metrics["total_cost_usd"], 4),
            "model_distribution": dict(metrics["model_usage"]),
            "category_distribution": dict(metrics["category_usage"]),
            "routing_mode_distribution": dict(metrics["routing_mode_usage"]),
            "circuit_breaker": circuit_breaker.get_status(),
            "config": {
                "routing_mode": ROUTING_MODE,
                "ollama_url": OLLAMA_BASE_URL,
                "ollama_model": OLLAMA_ROUTER_MODEL,
                "categories": list(model_mappings.keys())
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
        "model_mappings": model_mappings,
        "keywords": category_keywords,
        "custom_categories": custom_categories,
        "model_costs": MODEL_COSTS
    }

@app.post("/config/category")
async def add_category(config: CategoryConfig):
    """Add or update a category"""
    model_mappings[config.name] = config.models
    if config.keywords:
        category_keywords[config.name] = config.keywords
    if config.description:
        if config.name not in custom_categories:
            custom_categories[config.name] = {}
        custom_categories[config.name]["description"] = config.description
        custom_categories[config.name]["models"] = config.models
        if config.keywords:
            custom_categories[config.name]["keywords"] = config.keywords
    
    save_config()
    return {"status": "ok", "category": config.name, "models": config.models}

@app.post("/config/model-mapping")
async def update_model_mapping(update: ModelMappingUpdate):
    """Update models for a category"""
    if update.category not in model_mappings:
        raise HTTPException(404, f"Category '{update.category}' not found")
    
    model_mappings[update.category] = update.models
    save_config()
    return {"status": "ok", "category": update.category, "models": update.models}

@app.delete("/config/category/{category_name}")
async def delete_category(category_name: str):
    """Delete a custom category"""
    if category_name in DEFAULT_MODEL_MAPPINGS:
        raise HTTPException(400, "Cannot delete default category")
    
    if category_name in model_mappings:
        del model_mappings[category_name]
    if category_name in category_keywords:
        del category_keywords[category_name]
    if category_name in custom_categories:
        del custom_categories[category_name]
    
    save_config()
    return {"status": "ok", "deleted": category_name}

@app.post("/circuit-breaker/reset/{model}")
async def reset_circuit(model: str):
    """Manually reset circuit breaker for a model"""
    circuit_breaker.record_success(model)
    return {"status": "ok", "model": model}

@app.post("/v1/chat/completions")
@app.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured")
    
    print(f"Request: model={request.model}, messages={len(request.messages)}, tools={len(request.tools) if request.tools else 0}")
    
    start_time = time.time()
    
    session_id = request.user or "default_session"
    has_tools = request.tools is not None and len(request.tools) > 0
    
    category, routing_mode = await route_message(
        [msg.model_dump() for msg in request.messages],
        session_id,
        has_tools
    )
    
    models_to_try = model_mappings.get(category, model_mappings.get("conversation", [DEFAULT_MODEL]))
    
    last_error = None
    last_model_tried = None
    
    for selected_model in models_to_try:
        # Check circuit breaker
        if not circuit_breaker.is_available(selected_model):
            print(f"Skipping {selected_model} - circuit open")
            continue
        
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
                
                result = response.json()
                
                # Estimate cost
                usage = result.get("usage", {})
                cost = estimate_cost(
                    selected_model,
                    usage.get("prompt_tokens", 0),
                    usage.get("completion_tokens", 0)
                )
                
                latency_ms = (time.time() - start_time) * 1000
                track_request(category, selected_model, latency_ms, True, routing_mode, cost)
                
                # Reset circuit breaker on success
                circuit_breaker.record_success(selected_model)
                
                current_model_per_session[session_id] = selected_model
                
                return result
            except Exception as e:
                last_error = str(e)
                circuit_breaker.record_failure(selected_model)
                continue
    
    latency_ms = (time.time() - start_time) * 1000
    track_request(category, last_model_tried or "unknown", latency_ms, False, routing_mode, 0, last_error)
    
    raise HTTPException(status_code=500, detail=f"All models failed. Last error: {last_error}")

@app.on_event("startup")
async def startup_event():
    print(f"LLM Router v0.4.0 started")
    print(f"Routing mode: {ROUTING_MODE}")
    print(f"Ollama: {OLLAMA_BASE_URL} ({OLLAMA_ROUTER_MODEL})")
    print(f"Categories: {list(model_mappings.keys())}")
