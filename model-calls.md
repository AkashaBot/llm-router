# Model Calls

## Fonction

Gestion des appels aux différents modèles LLM cibles via OpenRouter.

## Modèles actuels (Phase 2)

| Catégorie | Modèle principal | Fallback 1 | Fallback 2 |
|-----------|-----------------|------------|------------|
| **tools** | aurora-alpha | kimi-k2.5 | glm-5 |
| **code** | glm-5 | aurora-alpha | gpt-4o-mini |
| **reasoning** | aurora-alpha | glm-5 | kimi-k2.5 |
| **conversation** | glm-5 | gpt-4o-mini | aurora-alpha |

## Configuration

```python
MODEL_MAPPINGS = {
    "tools": ["openrouter/aurora-alpha", "moonshotai/kimi-k2.5", "z-ai/glm-5"],
    "code": ["z-ai/glm-5", "openrouter/aurora-alpha", "openai/gpt-4o-mini"],
    "reasoning": ["openrouter/aurora-alpha", "z-ai/glm-5", "moonshotai/kimi-k2.5"],
    "conversation": ["z-ai/glm-5", "openai/gpt-4o-mini", "openrouter/aurora-alpha"]
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
            "tools": request.tools,  # Support function calling
            "tool_choice": request.tool_choice
        }
    )
```

## Fallback logic

```python
for model in models_to_try:
    try:
        response = await call_model(model, request)
        return response
    except Exception as e:
        log_error(model, e)
        continue  # Try next model

# All models failed
raise HTTPException(500, f"All models failed. Last error: {last_error}")
```

## Provider unique

Actuellement, seul OpenRouter est utilisé comme provider. Les modèles sont spécifiés avec leur chemin complet:
- `openrouter/aurora-alpha`
- `z-ai/glm-5`
- `moonshotai/kimi-k2.5`
- `openai/gpt-4o-mini`

## Points d'amélioration

- [ ] Ajouter support multi-provider (Anthropic direct, OpenAI direct)
- [ ] Implémenter circuit breaker
- [ ] Ajouter retry avec backoff
- [ ] Cache pour requêtes identiques
