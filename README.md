# LLM Router

Service de routage intelligent pour les requêtes LLM. Choix automatique du meilleur modèle selon le type de tâche (code, reasoning, conversation, tools, custom).

## État du projet

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Forward-only vers OpenRouter | ✅ Complète |
| Phase 2 | Routing par keywords + monitoring | ✅ Complète |
| Phase 3 | Routing LLM-based (Ollama/API) | ✅ Complète |

## Fonctionnalités

- **Routing intelligent** via Ollama (qwen2.5:0.5b) ou API
- **Circuit breaker** - désactive automatiquement les modèles défaillants
- **Métriques de coût** - estimation USD par requête
- **Catégories personnalisables** - ajoutez vos propres cas d'usage
- **Support function calling** - détection automatique des tools

## Démarrage rapide

```bash
cd service
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec votre OPENROUTER_API_KEY
uvicorn main:app --host 0.0.0.0 --port 3456
```

## Endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/v1/chat/completions` | OpenAI-compatible chat completions |
| POST | `/chat/completions` | Alias (compatibilité OpenClaw) |
| GET | `/health` | Health check |
| GET | `/metrics` | Métriques (requests, latence, coût, circuit breaker) |
| GET | `/config` | Configuration actuelle |
| POST | `/config/category` | Ajouter/modifier une catégorie |
| POST | `/config/model-mapping` | Modifier les modèles d'une catégorie |
| DELETE | `/config/category/{name}` | Supprimer une catégorie personnalisée |
| POST | `/circuit-breaker/reset/{model}` | Réinitialiser le circuit breaker |

## Configuration

### Variables d'environnement

```bash
# OpenRouter API
OPENROUTER_API_KEY=sk-or-v1-...

# Routing mode: "ollama" | "api" | "hybrid" | "keywords"
ROUTING_MODE=hybrid

# Ollama (pour routing LLM)
OLLAMA_BASE_URL=http://192.168.1.168:11434
OLLAMA_ROUTER_MODEL=qwen2.5:0.5b

# API routing fallback
ROUTER_API_MODEL=qwen/qwen3-1.7b
```

## Routing

Détection par Ollama/API avec fallback keywords:

| Catégorie | Détection | Modèles (fallback chain) |
|-----------|-----------|--------------------------|
| **tools** | `request.tools` présent | aurora-alpha → kimi-k2.5 → glm-5 |
| **code** | keywords: python, function... | glm-5 → aurora-alpha → gpt-4o-mini |
| **reasoning** | keywords: why, how, explain... | aurora-alpha → glm-5 → kimi-k2.5 |
| **conversation** | messages courts | glm-5 → gpt-4o-mini → aurora-alpha |
| **custom** | défini par l'utilisateur | configurable via API |

## Circuit Breaker

Désactive automatiquement un modèle après 3 erreurs consécutives:
- Réessaie après 5 minutes (half-open)
- Reset manuel via `/circuit-breaker/reset/{model}`

## Ajouter une catégorie personnalisée

```bash
curl -X POST http://localhost:3456/config/category \
  -H "Content-Type: application/json" \
  -d '{
    "name": "creative",
    "models": ["openrouter/aurora-alpha", "z-ai/glm-5"],
    "keywords": ["story", "poem", "creative", "fiction"],
    "description": "Creative writing tasks"
  }'
```

## Métriques

```bash
curl http://localhost:3456/metrics
```

Retourne:
- Nombre de requêtes (total/succès/échec)
- Latence moyenne
- **Coût total estimé (USD)**
- Distribution par modèle et catégorie
- État du circuit breaker
- 10 dernières requêtes

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
    ├── .env.example         # Config exemple
    └── router_config.json   # Config sauvegardée
```

## Coûts estimés (USD/1M tokens)

| Modèle | Input | Output |
|--------|-------|--------|
| aurora-alpha | $0.15 | $0.60 |
| kimi-k2.5 | $0.10 | $0.30 |
| glm-5 | $0.05 | $0.15 |
| gpt-4o-mini | $0.15 | $0.60 |
| gpt-4o | $2.50 | $10.00 |
