# Référence API

## Chat Completions

### POST /v1/chat/completions
### POST /chat/completions (alias OpenClaw)

Requête OpenAI-compatible.

**Request:**
```json
{
  "model": "router",
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "tools": [...],  // Optionnel
  "temperature": 0.7
}
```

**Response:**
```json
{
  "id": "gen-xxx",
  "model": "z-ai/glm-5",
  "choices": [...],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20
  }
}
```

---

## Monitoring

### GET /health

Health check basique.

**Response:**
```json
{
  "status": "healthy",
  "service": "llm-router",
  "version": "0.4.0",
  "routing_mode": "hybrid",
  "categories": ["tools", "code", "reasoning", "conversation"]
}
```

### GET /metrics

Métriques complètes.

**Response:**
```json
{
  "requests": {
    "total": 100,
    "success": 98,
    "failed": 2
  },
  "avg_latency_ms": 1234.56,
  "total_cost_usd": 0.45,
  "model_distribution": {"glm-5": 50, "kimi-k2.5": 48},
  "category_distribution": {"code": 60, "conversation": 38},
  "routing_mode_distribution": {"ollama": 80, "keywords": 18},
  "circuit_breaker": {
    "failures": {},
    "open_circuits": {},
    "config": {
      "failure_threshold": 3,
      "recovery_timeout_sec": 300
    }
  },
  "recent_requests": [...]
}
```

---

## Configuration

### GET /config

Configuration actuelle.

**Response:**
```json
{
  "routing_mode": "hybrid",
  "ollama": {"base_url": "...", "model": "qwen2.5:0.5b"},
  "model_mappings": {...},
  "keywords": {...},
  "model_costs": {...}
}
```

### POST /config/category

Créer ou modifier une catégorie.

**Request:**
```json
{
  "name": "creative",
  "models": ["moonshotai/kimi-k2.5"],
  "keywords": ["story", "poem"],
  "description": "Creative writing"
}
```

**Response:**
```json
{"status": "ok", "category": "creative", "models": [...]}
```

### POST /config/model-mapping

Modifier les modèles d'une catégorie.

**Request:**
```json
{
  "category": "code",
  "models": ["glm-5", "kimi-k2.5", "gpt-4o-mini"]
}
```

### DELETE /config/category/{name}

Supprimer une catégorie personnalisée.

---

## Circuit Breaker

### POST /circuit-breaker/reset/{model}

Reset un modèle spécifique.

**Example:**
```bash
curl -X POST http://localhost:3456/circuit-breaker/reset/moonshotai/kimi-k2.5
```

### POST /circuit-breaker/reset-all

Reset tous les circuits.

---

## Codes d'erreur

| Code | Cause | Solution |
|------|-------|----------|
| 422 | Validation error | Voir `validation_errors.log` |
| 500 | All models failed | Reset circuit breaker |
| 503 | Service unavailable | Vérifier si router actif |
