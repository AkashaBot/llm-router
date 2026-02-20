# Référence API

## Chat Completions

### POST /v1/chat/completions
### POST /chat/completions

**Request:**
```json
{
  "model": "router",
  "messages": [{"role": "user", "content": "Hello"}],
  "tools": [...]
}
```

**Response:**
```json
{
  "id": "gen-xxx",
  "model": "openrouter/z-ai/glm-5",
  "choices": [...],
  "usage": {"prompt_tokens": 10, "completion_tokens": 20}
}
```

---

## Providers

### GET /providers

Liste des providers configurés.

**Response:**
```json
{
  "providers": {
    "openrouter": {"base_url": "...", "configured": true},
    "openai": {"base_url": "...", "configured": false},
    "anthropic": {"base_url": "...", "configured": true},
    "ollama": {"base_url": "...", "configured": true}
  },
  "default_provider": "openrouter"
}
```

---

## Monitoring

### GET /health

```json
{
  "status": "healthy",
  "version": "0.5.0",
  "providers": ["openrouter", "openai", "anthropic", "google", "ollama"],
  "categories": ["tools", "code", "reasoning", "conversation"]
}
```

### GET /metrics

```json
{
  "requests": {"total": 100, "success": 98, "failed": 2},
  "avg_latency_ms": 1234,
  "total_cost_usd": 0.45,
  "model_distribution": {...},
  "provider_distribution": {
    "openrouter": 60,
    "openai": 30,
    "ollama": 10
  },
  "circuit_breaker": {...}
}
```

---

## Configuration

### GET /config

### POST /config/category

```json
{"name": "creative", "models": ["openrouter/kimi-k2.5"], "keywords": ["story"]}
```

### POST /config/model-mapping

```json
{"category": "code", "models": ["openai/gpt-4o", "anthropic/claude-3-sonnet"]}
```

### DELETE /config/category/{name}

---

## Circuit Breaker

### POST /circuit-breaker/reset/{model}

Reset un modèle: `POST /circuit-breaker/reset/openai/gpt-4o`

### POST /circuit-breaker/reset-all

Reset tous les circuits.

---

## Codes d'erreur

| Code | Cause |
|------|-------|
| 422 | Validation error |
| 500 | All models failed |
| 503 | Service unavailable |
