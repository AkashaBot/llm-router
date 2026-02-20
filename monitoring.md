# Monitoring & Metrics

## Endpoints

```bash
GET /metrics    # Métriques complètes
GET /health     # Health check basique
GET /config     # Configuration actuelle
```

## Métriques disponibles

### Vue d'ensemble

```json
{
  "requests": {
    "total": 1234,
    "success": 1200,
    "failed": 34
  },
  "avg_latency_ms": 1234.56,
  "total_cost_usd": 0.45,
  "model_distribution": {
    "z-ai/glm-5": 500,
    "openrouter/aurora-alpha": 400
  },
  "category_distribution": {
    "code": 600,
    "conversation": 400
  },
  "routing_mode_distribution": {
    "ollama": 800,
    "api": 200,
    "keywords": 234
  },
  "circuit_breaker": {
    "failures": {"aurora-alpha": 0},
    "open_circuits": {}
  }
}
```

### Par requête

```json
{
  "timestamp": "2026-02-20T00:00:00Z",
  "category": "code",
  "model": "z-ai/glm-5",
  "latency_ms": 1234,
  "success": true,
  "routing_mode": "ollama",
  "cost_usd": 0.000123
}
```

## Coût estimé

Calculé à partir des tokens utilisés:

```python
MODEL_COSTS = {
    "openrouter/aurora-alpha": {"input": 0.15, "output": 0.60},
    "moonshotai/kimi-k2.5": {"input": 0.10, "output": 0.30},
    "z-ai/glm-5": {"input": 0.05, "output": 0.15},
    ...
}

def estimate_cost(model, input_tokens, output_tokens):
    costs = MODEL_COSTS.get(model, {"input": 0.05, "output": 0.15})
    input_cost = (input_tokens / 1_000_000) * costs["input"]
    output_cost = (output_tokens / 1_000_000) * costs["output"]
    return input_cost + output_cost
```

## Circuit Breaker Status

```json
{
  "circuit_breaker": {
    "failures": {
      "aurora-alpha": 3,
      "glm-5": 0
    },
    "open_circuits": {
      "aurora-alpha": true
    },
    "last_failure": {
      "aurora-alpha": "2026-02-20T00:30:00Z"
    }
  }
}
```

## Logs

Logs stdout via uvicorn:

```
INFO: LLM Router v0.4.0 started
INFO: Routing mode: hybrid
INFO: Ollama: http://192.168.1.168:11434 (qwen2.5:0.5b)
INFO: Categories: ['tools', 'code', 'reasoning', 'conversation']
INFO: Request: model=router, messages=5, tools=2
INFO: POST /chat/completions HTTP/1.1" 200 OK
```

## Configuration actuelle

```bash
GET /config
```

Retourne:
- `routing_mode`: Mode actif
- `ollama`: URL et modèle
- `model_mappings`: Tous les mappings
- `keywords`: Keywords par catégorie
- `custom_categories`: Catégories personnalisées
- `model_costs`: Grille tarifaire

## Stockage

- **In-memory**: Métriques temps réel (100 dernières requêtes)
- **Fichier**: `router_config.json` (catégories et mappings personnalisés)

## Alerting (à venir)

- [ ] Alerte si taux d'erreur > 5%
- [ ] Alerte si latence moyenne > 5s
- [ ] Notification si circuit breaker déclenché
- [ ] Seuil de coût journalier
