# Model Calls

## Fonction

Gestion des appels aux différents modèles LLM cibles via OpenRouter.

## Modèles actuels

| Catégorie | Modèle principal | Fallback 1 | Fallback 2 |
|-----------|-----------------|------------|------------|
| **tools** | aurora-alpha | kimi-k2.5 | glm-5 |
| **code** | glm-5 | aurora-alpha | gpt-4o-mini |
| **reasoning** | aurora-alpha | glm-5 | kimi-k2.5 |
| **conversation** | glm-5 | gpt-4o-mini | aurora-alpha |

## Configuration dynamique

Les mappings sont modifiables via API:

```bash
POST /config/model-mapping
{
  "category": "code",
  "models": ["glm-5", "kimi-k2.5", "aurora-alpha"]
}
```

Ou en modifiant `router_config.json`:

```json
{
  "model_mappings": {
    "code": ["z-ai/glm-5", "openrouter/aurora-alpha"],
    "custom": ["moonshotai/kimi-k2.5"]
  }
}
```

## Appels aux modèles

```python
async with httpx.AsyncClient(timeout=60.0) as client:
    response = await client.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": selected_model,
            "messages": messages,
            "tools": request.tools,
            "tool_choice": request.tool_choice
        }
    )
```

## Fallback logic avec circuit breaker

```python
for model in models_to_try:
    # Vérifier circuit breaker
    if not circuit_breaker.is_available(model):
        continue  # Modèle désactivé
    
    try:
        response = await call_model(model, request)
        circuit_breaker.record_success(model)
        return response
    except Exception as e:
        circuit_breaker.record_failure(model)
        continue  # Try next model
```

## Coûts estimés

| Modèle | Input ($/1M) | Output ($/1M) |
|--------|--------------|---------------|
| aurora-alpha | 0.15 | 0.60 |
| kimi-k2.5 | 0.10 | 0.30 |
| glm-5 | 0.05 | 0.15 |
| gpt-4o-mini | 0.15 | 0.60 |
| gpt-4o | 2.50 | 10.00 |
| qwen3-1.7b | 0.01 | 0.02 |

Estimation par requête:

```python
def estimate_cost(model, input_tokens, output_tokens):
    costs = MODEL_COSTS.get(model, {"input": 0.05, "output": 0.15})
    input_cost = (input_tokens / 1_000_000) * costs["input"]
    output_cost = (output_tokens / 1_000_000) * costs["output"]
    return input_cost + output_cost
```

## Provider unique

Actuellement, seul OpenRouter est utilisé comme provider. Les modèles sont spécifiés avec leur chemin complet:
- `openrouter/aurora-alpha`
- `z-ai/glm-5`
- `moonshotai/kimi-k2.5`
- `openai/gpt-4o-mini`

## Points d'amélioration

- [x] Circuit breaker implémenté
- [ ] Ajouter support multi-provider (Anthropic direct, OpenAI direct)
- [ ] Cache pour requêtes identiques
- [ ] Retry avec backoff exponentiel
