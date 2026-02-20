# LLM Router

Service de routage intelligent pour les requêtes LLM. Choix automatique du meilleur modèle selon le type de tâche (code, reasoning, conversation, tools).

## État du projet

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Forward-only vers OpenRouter | ✅ Complète |
| Phase 2 | Routing par keywords + monitoring | ✅ Complète |
| Phase 3 | Routing LLM-based (Ollama/API) | 🔄 En cours |

## Démarrage rapide

```bash
cd service
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec votre OPENROUTER_API_KEY
uvicorn main:app --host 0.0.0.0 --port 3456
```

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /v1/chat/completions` | OpenAI-compatible chat completions |
| `POST /chat/completions` | Alias (compatibilité OpenClaw) |
| `GET /health` | Health check |
| `GET /metrics` | Métriques (requests, latence, coût, circuit breaker) |
| `GET /config` | Configuration actuelle |
| `POST /config/category` | Ajouter/modifier une catégorie |
| `POST /config/model-mapping` | Modifier les modèles d'une catégorie |
| `DELETE /config/category/{name}` | Supprimer une catégorie personnalisée |
| `POST /circuit-breaker/reset/{model}` | Réinitialiser le circuit breaker |

## Routing actuel

Détection par keywords + support tools:

| Catégorie | Détection | Modèles (fallback chain) |
|-----------|-----------|--------------------------|
| **tools** | `request.tools` présent | aurora-alpha → kimi-k2.5 → glm-5 |
| **code** | keywords: python, function, debug... | glm-5 → aurora-alpha → gpt-4o-mini |
| **reasoning** | keywords: why, how, explain... | aurora-alpha → glm-5 → kimi-k2.5 |
| **conversation** | messages courts, hello, thanks... | glm-5 → gpt-4o-mini → aurora-alpha |

## Configuration OpenClaw

Ajouter dans `~/.openclaw/openclaw.json`:

```json
{
  "models": {
    "providers": {
      "router": {
        "baseUrl": "http://localhost:3456",
        "apiKey": "local-router",
        "api": "openai-completions",
        "models": [{ "id": "router", "name": "LLM Router" }]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "router/router"
      }
    }
  }
}
```

## Architecture

```
llm-router/
├── README.md                # Ce fichier
├── overview.md              # Vue d'ensemble
├── steps.md                 # Étapes de développement
├── routing-engine.md        # Moteur de routing
├── model-calls.md           # Appels aux modèles
├── fallback-guardrails.md   # Fallbacks et sécurités
├── monitoring.md            # Métriques
├── integration.md           # Intégration OpenClaw
└── service/
    ├── main.py              # Service FastAPI
    ├── requirements.txt     # Dépendances Python
    └── .env.example         # Config exemple
```

## Monitoring

```bash
curl http://localhost:3456/metrics
```

Retourne:
- Nombre de requêtes (total/succès/échec)
- Latence moyenne
- Distribution par modèle et catégorie
- 10 dernières requêtes
