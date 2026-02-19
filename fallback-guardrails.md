# Fallbacks & Guardrails

## Fallback Chain (implémenté)

```
Requête → Détection catégorie
    ↓
Modèle primaire disponible ? → Appeler
    ↓ Échec
Fallback 1 → Appeler
    ↓ Échec
Fallback 2 → Appeler
    ↓ Échec
Retourner erreur avec contexte
```

## Implémentation actuelle

```python
for model in models_to_try:
    try:
        response = await call_model(model, request)
        track_request(category, model, latency, success=True)
        return response
    except Exception:
        continue

# All failed
track_request(category, last_model, latency, success=False, error=last_error)
raise HTTPException(500, detail=f"All models failed. Last error: {last_error}")
```

## Guardrails à implémenter

### Circuit Breaker
```python
# Si un modèle a > N erreurs consécutives, le marquer "unhealthy"
circuit_breaker = {
    "openrouter/aurora-alpha": {"failures": 0, "healthy": True},
    "z-ai/glm-5": {"failures": 0, "healthy": True},
    ...
}

def should_try_model(model: str) -> bool:
    return circuit_breaker[model]["healthy"]
```

### Timeout par modèle
```python
# Timeout configurable par modèle
TIMEOUTS = {
    "default": 60.0,
    "aurora-alpha": 45.0,  # Plus rapide
    "kimi-k2.5": 90.0      # Peut être plus lent
}
```

### Rate limiting
- Détecter erreurs 429 (rate limit)
- Attendre avant retry ou passer au suivant

## Error handling

| Error type | Action |
|------------|--------|
| Rate limit (429) | Passer au modèle suivant |
| Auth error (401) | Logger + passer au suivant |
| Timeout | Passer au suivant |
| 5xx | Passer au suivant |
| Parse error | Logger + retourner erreur |

## Metrics tracking

Chaque requête est trackée:
```python
{
    "timestamp": "2026-02-20T00:00:00Z",
    "category": "code",
    "model": "z-ai/glm-5",
    "latency_ms": 1234,
    "success": true
}
```

Accessible via `GET /metrics`.
