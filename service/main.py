# LLM Router Service - v0.5.0: Multi-provider support
"""
Routing intelligent avec:
- Multi-provider: OpenRouter, OpenAI, Anthropic, Google, Ollama
- Modes: ollama | api | hybrid | keywords
- Circuit breaker persistant
- Métriques de coût estimé
- Configuration utilisateur des modèles et catégories
"""
import os
import re
import time
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple, Literal
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
import httpx
from dotenv import load_dotenv
from collections import defaultdict
import threading

load_dotenv()

app = FastAPI(title="LLM Router", version="0.5.0")

# =============================================================================
# MIDDLEWARE
# =============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.url.path in ["/chat/completions", "/v1/chat/completions"]:
        try:
            body = await request.body()
            print(f"[REQUEST] {request.url.path} ({len(body)} bytes)")
        except:
            pass
    return await call_next(request)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    try:
        errors = exc.errors()
        with open("validation_errors.log", "a", encoding="utf-8") as f:
            f.write(f"\n--- {datetime.utcnow().isoformat()} ---\n")
            json.dump(errors, f, indent=2, ensure_ascii=False)
        errors_summary = json.dumps([{"loc": list(e.get("loc", [])), "type": e.get("type")} for e in errors])
    except Exception as e:
        errors_summary = f"validation error: {str(e)[:100]}"
    return JSONResponse(status_code=422, content={"detail": errors_summary})

# =============================================================================
# PROVIDERS CONFIGURATION
# =============================================================================

PROVIDERS = {
    "openrouter": {
        "base_url": os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        "api_key": os.getenv("OPENROUTER_API_KEY", ""),
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "models_prefix": "",  # Models are referenced as-is
    },
    "openai": {
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "models_prefix": "",
    },
    "anthropic": {
        "base_url": os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1"),
        "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "auth_header": "x-api-key",
        "auth_prefix": "",
        "models_prefix": "",
        "requires_version": True,
    },
    "google": {
        "base_url": os.getenv("GOOGLE_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
        "api_key": os.getenv("GOOGLE_API_KEY", ""),
        "auth_header": "x-goog-api-key",
        "auth_prefix": "",
        "models_prefix": "models/",
    },
    "ollama": {
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "api_key": "",  # Ollama doesn't need API key
        "auth_header": None,
        "auth_prefix": "",
        "models_prefix": "",
        "use_generate_api": True,  # Ollama uses /api/generate
    },
}

ROUTING_MODE = os.getenv("ROUTING_MODE", "hybrid")
OLLAMA_ROUTER_MODEL = os.getenv("OLLAMA_ROUTER_MODEL", "qwen2.5:0.5b")
ROUTER_API_MODEL = os.getenv("ROUTER_API_MODEL", "qwen/qwen3-1.7b")
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "openrouter")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "z-ai/glm-5")

# =============================================================================
# COST ESTIMATES (USD per 1M tokens)
# =============================================================================

MODEL_COSTS = {
    # OpenRouter models
    "openrouter/moonshotai/kimi-k2.5": {"input": 0.60, "output": 3.00},
    "openrouter/z-ai/glm-5": {"input": 0.05, "output": 0.15},
    "openrouter/qwen/qwen3-1.7b": {"input": 0.01, "output": 0.02},
    # OpenAI models
    "openai/gpt-4o": {"input": 2.50, "output": 10.00},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "openai/gpt-4-turbo": {"input": 10.00, "output": 30.00},
    # Anthropic models
    "anthropic/claude-3-opus": {"input": 15.00, "output": 75.00},
    "anthropic/claude-3-sonnet": {"input": 3.00, "output": 15.00},
    "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},
    # Google models
    "google/gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "google/gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    # Ollama (free)
    "ollama/llama3.1": {"input": 0, "output": 0},
    "ollama/qwen2.5": {"input": 0, "output": 0},
}

# =============================================================================
# USER CONFIG
# =============================================================================

CONFIG_FILE = os.getenv("ROUTER_CONFIG_FILE", "router_config.json")

DEFAULT_MODEL_MAPPINGS = {
    "tools": [
        "openrouter/moonshotai/kimi-k2.5",
        "openrouter/z-ai/glm-5",
        "openai/gpt-4o-mini"
    ],
    "code": [
        "openrouter/z-ai/glm-5",
        "openai/gpt-4o-mini",
        "openrouter/moonshotai/kimi-k2.5"
    ],
    "reasoning": [
        "openrouter/moonshotai/kimi-k2.5",
        "openrouter/z-ai/glm-5",
        "openai/gpt-4o-mini"
    ],
    "conversation": [
        "openrouter/z-ai/glm-5",
        "openai/gpt-4o-mini",
        "openrouter/moonshotai/kimi-k2.5"
    ]
}

DEFAULT_KEYWORDS = {
    "code": ["code", "python", "javascript", "function", "class", "def ", "import ", "bug", "debug", "error", "refactor", "api", "git"],
    "reasoning": ["why", "how", "explain", "analyze", "think", "reason", "prove", "math", "calculate", "logic"],
    "conversation": ["hello", "hi", "hey", "thanks", "thank you", "please", "sorry", "yes", "no", "ok", "okay", "sure"]
}

model_mappings: Dict[str, List[str]] = {}
category_keywords: Dict[str, List[str]] = {}
custom_categories: Dict[str, Dict] = {}

def load_config():
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
            print(f"Config loaded from {CONFIG_FILE}")
        except Exception as e:
            print(f"Error loading config: {e}")

def save_config():
    config = {
        "model_mappings": model_mappings,
        "keywords": category_keywords,
        "custom_categories": custom_categories
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

load_config()

# =============================================================================
# CIRCUIT BREAKER WITH PERSISTENCE
# =============================================================================

CIRCUIT_BREAKER_FILE = os.path.join(os.path.dirname(__file__), "circuit_breaker_state.json")

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout_sec: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_sec
        self.failures: Dict[str, int] = defaultdict(int)
        self.last_failure: Dict[str, float] = {}
        self.open_circuits: Dict[str, bool] = {}
        self.lock = threading.Lock()
        self._load_state()
    
    def _load_state(self):
        if os.path.exists(CIRCUIT_BREAKER_FILE):
            try:
                with open(CIRCUIT_BREAKER_FILE, "r") as f:
                    state = json.load(f)
                self.failures = defaultdict(int, state.get("failures", {}))
                self.last_failure = {k: float(v) for k, v in state.get("last_failure", {}).items()}
                self.open_circuits = state.get("open_circuits", {})
                print(f"Circuit breaker state loaded")
            except Exception as e:
                print(f"Error loading circuit breaker: {e}")
    
    def _save_state(self):
        try:
            state = {
                "failures": dict(self.failures),
                "last_failure": self.last_failure,
                "open_circuits": self.open_circuits,
                "updated_at": datetime.utcnow().isoformat()
            }
            with open(CIRCUIT_BREAKER_FILE, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Error saving circuit breaker: {e}")
    
    def record_failure(self, model: str):
        with self.lock:
            self.failures[model] += 1
            self.last_failure[model] = time.time()
            if self.failures[model] >= self.failure_threshold:
                self.open_circuits[model] = True
                print(f"Circuit OPEN for {model}")
            self._save_state()
    
    def record_success(self, model: str):
        with self.lock:
            self.failures[model] = 0
            self.open_circuits[model] = False
            self._save_state()
    
    def is_available(self, model: str) -> bool:
        with self.lock:
            if model not in self.open_circuits or not self.open_circuits[model]:
                return True
            if model in self.last_failure:
                elapsed = time.time() - self.last_failure[model]
                if elapsed > self.recovery_timeout:
                    return True
            return False
    
    def get_status(self) -> Dict:
        with self.lock:
            return {
                "failures": dict(self.failures),
                "open_circuits": {k: v for k, v in self.open_circuits.items() if v},
                "last_failure": {k: datetime.fromtimestamp(v).isoformat() for k, v in self.last_failure.items()},
                "config": {"failure_threshold": self.failure_threshold, "recovery_timeout_sec": self.recovery_timeout}
            }
    
    def reset_all(self):
        with self.lock:
            self.failures.clear()
            self.last_failure.clear()
            self.open_circuits.clear()
            self._save_state()

circuit_breaker = CircuitBreaker()

# =============================================================================
# METRICS
# =============================================================================

metrics_lock = threading.Lock()
metrics = {
    "requests_total": 0, "requests_success": 0, "requests_failed": 0,
    "model_usage": defaultdict(int), "category_usage": defaultdict(int),
    "provider_usage": defaultdict(int), "routing_mode_usage": defaultdict(int),
    "total_latency_ms": 0, "total_cost_usd": 0.0, "recent_requests": []
}

def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    costs = MODEL_COSTS.get(model, {"input": 0.05, "output": 0.15})
    return (input_tokens / 1_000_000) * costs["input"] + (output_tokens / 1_000_000) * costs["output"]

def track_request(category: str, model: str, latency_ms: float, success: bool, 
                  routing_mode: str = "keywords", cost_usd: float = 0.0, provider: str = None, error: str = None):
    with metrics_lock:
        metrics["requests_total"] += 1
        if success:
            metrics["requests_success"] += 1
        else:
            metrics["requests_failed"] += 1
        metrics["model_usage"][model] += 1
        metrics["category_usage"][category] += 1
        if provider:
            metrics["provider_usage"][provider] += 1
        metrics["routing_mode_usage"][routing_mode] += 1
        metrics["total_latency_ms"] += latency_ms
        metrics["total_cost_usd"] += cost_usd
        
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "category": category, "model": model, "provider": provider,
            "latency_ms": round(latency_ms, 2), "success": success,
            "routing_mode": routing_mode, "cost_usd": round(cost_usd, 6)
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
    content: Any
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

Catégories disponibles: {categories}

Réponds UNIQUEMENT avec le nom de la catégorie."""

def parse_model_id(model_id: str) -> Tuple[str, str]:
    """Parse 'provider/model' or 'model' (default provider)"""
    if "/" in model_id:
        parts = model_id.split("/", 1)
        return parts[0], parts[1]
    return DEFAULT_PROVIDER, model_id

def detect_category_keywords(message: str) -> str:
    message_lower = message.lower()
    for cat_name, cat_config in custom_categories.items():
        for keyword in cat_config.get("keywords", []):
            if keyword.lower() in message_lower:
                return cat_name
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword.lower() in message_lower:
                return category
    return "conversation"

async def route_with_ollama(message: str) -> Tuple[str, str]:
    categories = list(model_mappings.keys())
    prompt = ROUTER_PROMPT.format(categories=", ".join(categories))
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(
                f"{PROVIDERS['ollama']['base_url']}/api/generate",
                json={"model": OLLAMA_ROUTER_MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.1, "num_predict": 20}}
            )
            response.raise_for_status()
            category = response.json().get("response", "").strip().lower().split()[0]
            if category in model_mappings:
                return category, "ollama"
        except Exception as e:
            print(f"Ollama routing failed: {e}")
    raise Exception("Ollama routing failed")

async def route_with_api(message: str) -> Tuple[str, str]:
    categories = list(model_mappings.keys())
    prompt = ROUTER_PROMPT.format(categories=", ".join(categories))
    
    provider, model = parse_model_id(ROUTER_API_MODEL)
    prov_config = PROVIDERS.get(provider, PROVIDERS["openrouter"])
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            headers = {"Content-Type": "application/json"}
            if prov_config.get("api_key"):
                headers[prov_config["auth_header"]] = prov_config["auth_prefix"] + prov_config["api_key"]
            
            response = await client.post(
                f"{prov_config['base_url']}/chat/completions",
                headers=headers,
                json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 20, "temperature": 0.1}
            )
            response.raise_for_status()
            category = response.json()["choices"][0]["message"]["content"].strip().lower().split()[0]
            if category in model_mappings:
                return category, "api"
        except Exception as e:
            print(f"API routing failed: {e}")
    raise Exception("API routing failed")

async def route_message(messages: List[Dict], session_id: str, has_tools: bool = False) -> Tuple[str, str]:
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
    
    # Short continuation check
    if isinstance(last_user_msg, str) and len(last_user_msg.split()) < 4:
        return "conversation", "continuation"
    
    if ROUTING_MODE in ["ollama", "hybrid"]:
        try:
            category, mode = await route_with_ollama(last_user_msg)
            if ROUTING_MODE == "ollama":
                return category, mode
        except:
            pass
    
    if ROUTING_MODE in ["api", "hybrid"]:
        try:
            return await route_with_api(last_user_msg)
        except:
            pass
    
    return detect_category_keywords(last_user_msg), "keywords"

# =============================================================================
# MODEL CALLING
# =============================================================================

async def call_model(model_id: str, request: ChatCompletionRequest) -> Tuple[Dict, str]:
    """Call a model via the appropriate provider. Returns (response, provider_name)"""
    provider, model_name = parse_model_id(model_id)
    prov_config = PROVIDERS.get(provider)
    
    if not prov_config:
        raise ValueError(f"Unknown provider: {provider}")
    
    if not prov_config.get("api_key") and provider != "ollama":
        raise ValueError(f"No API key configured for provider: {provider}")
    
    headers = {"Content-Type": "application/json"}
    if prov_config.get("api_key") and prov_config.get("auth_header"):
        headers[prov_config["auth_header"]] = prov_config["auth_prefix"] + prov_config["api_key"]
    
    # Handle Anthropic's required version header
    if prov_config.get("requires_version"):
        headers["anthropic-version"] = "2023-06-01"
    
    payload = {
        "model": prov_config.get("models_prefix", "") + model_name,
        "messages": [msg.model_dump(exclude_none=True) for msg in request.messages],
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "tools": request.tools,
        "tool_choice": request.tool_choice
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Ollama uses /api/generate or /api/chat
        if prov_config.get("use_generate_api"):
            # Convert to Ollama format
            ollama_payload = {
                "model": model_name,
                "messages": payload["messages"],
                "stream": False,
                "options": {"temperature": payload.get("temperature", 1.0)}
            }
            response = await client.post(
                f"{prov_config['base_url']}/api/chat",
                headers={},
                json=ollama_payload
            )
        else:
            response = await client.post(
                f"{prov_config['base_url']}/chat/completions",
                headers=headers,
                json=payload
            )
        
        response.raise_for_status()
        return response.json(), provider

# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "llm-router",
        "version": "0.5.0",
        "routing_mode": ROUTING_MODE,
        "providers": list(PROVIDERS.keys()),
        "categories": list(model_mappings.keys())
    }

@app.get("/metrics")
async def get_metrics():
    with metrics_lock:
        avg_latency = metrics["total_latency_ms"] / metrics["requests_total"] if metrics["requests_total"] > 0 else 0
        return {
            "requests": {"total": metrics["requests_total"], "success": metrics["requests_success"], "failed": metrics["requests_failed"]},
            "avg_latency_ms": round(avg_latency, 2),
            "total_cost_usd": round(metrics["total_cost_usd"], 4),
            "model_distribution": dict(metrics["model_usage"]),
            "category_distribution": dict(metrics["category_usage"]),
            "provider_distribution": dict(metrics["provider_usage"]),
            "circuit_breaker": circuit_breaker.get_status(),
            "recent_requests": metrics["recent_requests"][-10:]
        }

@app.get("/config")
async def get_config():
    return {
        "routing_mode": ROUTING_MODE,
        "providers": {k: {"base_url": v["base_url"], "configured": bool(v.get("api_key"))} for k, v in PROVIDERS.items()},
        "model_mappings": model_mappings,
        "keywords": category_keywords,
        "custom_categories": custom_categories,
        "model_costs": MODEL_COSTS
    }

@app.get("/providers")
async def list_providers():
    return {
        "providers": {k: {"base_url": v["base_url"], "configured": bool(v.get("api_key"))} for k, v in PROVIDERS.items()},
        "default_provider": DEFAULT_PROVIDER
    }

@app.post("/config/category")
async def add_category(config: CategoryConfig):
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
    if update.category not in model_mappings:
        raise HTTPException(404, f"Category '{update.category}' not found")
    model_mappings[update.category] = update.models
    save_config()
    return {"status": "ok", "category": update.category, "models": update.models}

@app.delete("/config/category/{category_name}")
async def delete_category(category_name: str):
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

@app.post("/config/reload")
async def reload_config():
    """Reload configuration from file without restart"""
    if load_config():
        return {
            "status": "ok",
            "message": "Config reloaded",
            "categories": list(model_mappings.keys()),
            "model_mappings": model_mappings
        }
    raise HTTPException(500, "Failed to reload config")

@app.post("/circuit-breaker/reset/{model}")
async def reset_circuit(model: str):
    circuit_breaker.record_success(model)
    return {"status": "ok", "model": model}

@app.post("/circuit-breaker/reset-all")
async def reset_all_circuits():
    circuit_breaker.reset_all()
    return {"status": "ok", "message": "All circuits reset"}

@app.post("/v1/chat/completions")
@app.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    start_time = time.time()
    
    session_id = request.user or "default_session"
    has_tools = request.tools is not None and len(request.tools) > 0
    
    category, routing_mode = await route_message(
        [msg.model_dump() for msg in request.messages],
        session_id, has_tools
    )
    
    models_to_try = model_mappings.get(category, model_mappings.get("conversation", [f"{DEFAULT_PROVIDER}/{DEFAULT_MODEL}"]))
    
    last_error = None
    last_model_tried = None
    last_provider = None
    
    for model_id in models_to_try:
        if not circuit_breaker.is_available(model_id):
            print(f"Skipping {model_id} - circuit open")
            continue
        
        last_model_tried = model_id
        
        try:
            result, provider = await call_model(model_id, request)
            last_provider = provider
            
            usage = result.get("usage", {})
            cost = estimate_cost(model_id, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
            
            latency_ms = (time.time() - start_time) * 1000
            track_request(category, model_id, latency_ms, True, routing_mode, cost, provider)
            
            circuit_breaker.record_success(model_id)
            
            return result
        except Exception as e:
            last_error = str(e)
            circuit_breaker.record_failure(model_id)
            continue
    
    latency_ms = (time.time() - start_time) * 1000
    track_request(category, last_model_tried or "unknown", latency_ms, False, routing_mode, 0, last_provider, last_error)
    
    raise HTTPException(500, f"All models failed. Last error: {last_error}")

@app.on_event("startup")
async def startup_event():
    print(f"LLM Router v0.5.0 started")
    print(f"Routing mode: {ROUTING_MODE}")
    print(f"Providers: {list(PROVIDERS.keys())}")
    print(f"Categories: {list(model_mappings.keys())}")
