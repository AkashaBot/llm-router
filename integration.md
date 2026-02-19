# Intégration OpenClaw

## Type d'intégration

**Provider custom** - Le router est configuré comme un provider "virtuel" dans OpenClaw.

## Configuration appliquée

```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "router": {
        "baseUrl": "http://localhost:3456",
        "apiKey": "local-router",
        "api": "openai-completions",
        "models": [
          {
            "id": "router",
            "name": "LLM Router",
            "reasoning": true,
            "input": ["text"],
            "cost": {
              "input": 0,
              "output": 0,
              "cacheRead": 0,
              "cacheWrite": 0
            },
            "contextWindow": 200000,
            "maxTokens": 8192
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "router/router",
        "fallbacks": [
          "openrouter/openrouter/aurora-alpha",
          "openrouter/z-ai/glm-5",
          "nvidia-nim/moonshotai/kimi-k2.5"
        ]
      }
    }
  }
}
```

## Architecture

```
OpenClaw Gateway
       │
       ▼
   router/router (localhost:3456)
       │
       ├── Détection catégorie (keywords)
       │
       ▼
   OpenRouter API
       │
       ├── aurora-alpha
       ├── glm-5
       ├── kimi-k2.5
       └── gpt-4o-mini
```

## Démarrage

1. Lancer le service router:
```bash
cd plans/llm-router/service
uvicorn main:app --host 0.0.0.0 --port 3456
```

2. Configurer OpenClaw (si pas déjà fait):
```bash
# La config est dans ~/.openclaw/openclaw.json
openclaw gateway restart
```

## Endpoints compatibles

| Endpoint | Usage |
|----------|-------|
| `POST /v1/chat/completions` | Standard OpenAI |
| `POST /chat/completions` | Alias OpenClaw |
| `GET /health` | Health check |
| `GET /metrics` | Monitoring |

## Avantages de cette approche

- **Pas de modification du core OpenClaw** - juste de la config
- **Transparent** - les agents utilisent `router/router` comme n'importe quel modèle
- **Flexible** - on peut changer les mappings sans toucher à OpenClaw
- **Observable** - endpoint `/metrics` pour le monitoring

## Limitations actuelles

- Circuit breaker non implémenté
- Pas de métriques de coût
- Router basique (keywords) - Phase 3 (LLM) à venir
