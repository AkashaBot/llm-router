# Fallbacks & Guardrails

## Fallback Chain (implémenté)

```
Requête → Détection catégorie
    ↓
Modèle primaire disponible? (circuit breaker OK?)
    ↓ OUI → Appeler
    ↓ NON ou ÉCHEC
Fallback 1 → Appeler
    ↓ ÉCHEC
Fallback 2 → Appeler
    ↓ ÉCHEC
Retourner erreur avec contexte
```

## Circuit Breaker

Désactive automatiquement un modèle défaillant:

```python
class CircuitBreaker:
    failure_threshold = 3      # Seuil d'échecs
    recovery_timeout = 300     # 5 minutes avant retry
```

### Comportement

| État | Description |
|------|-------------|
| **CLOSED** | Fonctionnement normal |
| **OPEN** | Modèle désactivé (trop d'erreurs) |
| **HALF-OPEN** | Test après timeout (1 requête autorisée) |

### API

```bash
# Voir l'état
GET /metrics → circuit_breaker section

# Reset manuel
POST /circuit-breaker/reset/z-ai/glm-5
```

### Exemple de sortie

```json
{
  "circuit_breaker": {
    "failures": {"z-ai/glm-5": 0, "aurora-alpha": 3},
    "open_circuits": {"aurora-alpha": true},
    "last_failure": {"aurora-alpha": "2026-02-20T00:30:00"}
  }
}
```

## Error handling

| Error type | Action |
|------------|--------|
| Rate limit (429) | Passer au modèle suivant |
| Auth error (401) | Logger + passer au suivant |
| Timeout | Passer au suivant |
| 5xx | Passer au suivant |
| Validation (422) | Logger détails + erreur |

## Validation des requêtes

```python
class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    # ... autres champs
    
    class Config:
        extra = "ignore"  # Ignore les champs inconnus d'OpenClaw
```

Handler d'erreur détaillé:

```python
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)[:500]}
    )
```

## Metrics tracking

Chaque requête est trackée avec:

```python
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

## Garde-fous additionnels

- **Timeout global**: 60 secondes par requête
- **Timeout routing**: 15 secondes (Ollama), 10 secondes (API)
- **Max retries**: Nombre de modèles dans la fallback chain
- **Session continuity**: Messages courts gardent le même modèle
