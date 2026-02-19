# Monitoring & Metrics

## Endpoint

```bash
GET /metrics
```

## Métriques trackées

### Par requête
- Catégorie détectée (code/reasoning/conversation/tools)
- Modèle utilisé
- Latence (ms)
- Succès/échec
- Erreur (si échec)

### Agrégés

```json
{
  "requests": {
    "total": 1234,
    "success": 1200,
    "failed": 34
  },
  "avg_latency_ms": 1234.56,
  "model_distribution": {
    "z-ai/glm-5": 500,
    "openrouter/aurora-alpha": 400,
    "moonshotai/kimi-k2.5": 200
  },
  "category_distribution": {
    "code": 600,
    "conversation": 400,
    "reasoning": 150,
    "tools": 84
  },
  "recent_requests": [
    {
      "timestamp": "2026-02-20T00:00:00Z",
      "category": "code",
      "model": "z-ai/glm-5",
      "latency_ms": 1234,
      "success": true
    }
  ]
}
```

## Implémentation

```python
metrics = {
    "requests_total": 0,
    "requests_success": 0,
    "requests_failed": 0,
    "model_usage": defaultdict(int),
    "category_usage": defaultdict(int),
    "total_latency_ms": 0,
    "recent_requests": []  # Last 100
}

def track_request(category, model, latency_ms, success, error=None):
    with metrics_lock:
        metrics["requests_total"] += 1
        # ... update all counters
        metrics["recent_requests"].append(entry)
```

## Logs

Logs stdout via uvicorn:
```
INFO: POST /chat/completions HTTP/1.1" 200 OK
INFO: GET /metrics HTTP/1.1" 200 OK
```

## Dashboard (à venir)

Interface web pour visualiser les métriques:
- Graphique d'utilisation par modèle
- Latence P50/P95
- Alertes visuelles sur erreurs

## Alerting (à venir)

- Alerte si taux d'erreur > 5%
- Alerte si latence moyenne > 5s
- Notification si circuit breaker déclenché
