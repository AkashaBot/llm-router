# LLM Router - Vue d'ensemble

## Objectif

Système de routage intelligent qui choisit dynamiquement le meilleur modèle LLM pour chaque requête selon le contexte, tout en optimisant coût et latence.

## Architecture par composants

```
llm-router/
├── README.md                # Démarrage rapide
├── overview.md              # Ce fichier - vision globale
├── routing-engine.md        # Moteur de décision
├── model-calls.md           # Gestion des appels aux LLMs cibles
├── fallback-guardrails.md   # Fallbacks et sécurités
├── monitoring.md            # Cost/latence/metrics
├── integration.md           # Plugin OpenClaw (config provider)
└── service/
    ├── main.py              # Service FastAPI
    ├── requirements.txt     # Dépendances
    └── .env.example         # Config
```

## Phases de développement

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Forward-only vers OpenRouter | ✅ |
| Phase 2 | Routing par keywords + monitoring | ✅ |
| Phase 3 | Router LLM-based (Ollama/API) | ✅ |

## Décisions d'architecture

| Sujet | Décision | Status |
|-------|----------|--------|
| Scope | Par requête avec continuité intelligente | ✅ |
| Router | Ollama (qwen2.5:0.5b) + API fallback | ✅ |
| Fallback | Keywords (Phase 2) si LLM routing échoue | ✅ |
| Contexte | Dernier message utilisateur | ✅ |
| Intégration | Provider custom OpenClaw | ✅ |
| Support tools | Détection + routing spécialisé | ✅ |
| Circuit breaker | 3 erreurs → disable 5 min | ✅ |
| Coût | Estimation par requête | ✅ |
| Custom categories | API REST pour ajouter/modifier | ✅ |

## Catégories de routing

| Catégorie | Détection | Modèles |
|-----------|-----------|---------|
| **tools** | `request.tools` présent | aurora-alpha → kimi-k2.5 → glm-5 |
| **code** | keywords: python, function, debug... | glm-5 → aurora-alpha → gpt-4o-mini |
| **reasoning** | keywords: why, how, explain... | aurora-alpha → glm-5 → kimi-k2.5 |
| **conversation** | messages courts, hello, thanks... | glm-5 → gpt-4o-mini → aurora-alpha |
| **custom** | définies par l'utilisateur | configurable via API |

## Modes de routing

| Mode | Description |
|------|-------------|
| `ollama` | Utilise uniquement Ollama pour le routing |
| `api` | Utilise uniquement l'API pour le routing |
| `hybrid` | Ollama avec fallback API (recommandé) |
| `keywords` | Fallback Phase 2 uniquement |

## API de configuration

```bash
# Ajouter une catégorie
POST /config/category
{
  "name": "creative",
  "models": ["aurora-alpha", "glm-5"],
  "keywords": ["story", "poem"],
  "description": "Creative writing"
}

# Modifier les modèles d'une catégorie
POST /config/model-mapping
{
  "category": "code",
  "models": ["glm-5", "kimi-k2.5"]
}

# Supprimer une catégorie
DELETE /config/category/creative
```

## Intégration OpenClaw

Le router est configuré comme un provider custom:

```json
{
  "providers": {
    "router": {
      "baseUrl": "http://localhost:3456",
      "api": "openai-completions",
      "models": [{ "id": "router" }]
    }
  }
}
```

Le modèle primaire est `router/router` dans la config OpenClaw.

## Déploiement

- **Local**: `uvicorn main:app --port 3456`
- **Port**: 3456
- **Provider cible**: OpenRouter
- **Config sauvegardée**: `router_config.json`
