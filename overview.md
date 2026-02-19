# LLM Router - Vue d'ensemble

## Objectif

Système de routage intelligent qui choisit dynamiquement le meilleur modèle LLM pour chaque requête selon le contexte, tout en optimisant coût et latence.

## Architecture par composants

```
llm-router/
├── README.md                # Démarrage rapide
├── overview.md              # Ce fichier - vision globale
├── routing-engine.md        # Moteur de décision (keywords → LLM)
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
| Phase 3 | Router LLM-based (Qwen local) | 🔜 |

## Décisions d'architecture

| Sujet | Décision | Status |
|-------|----------|--------|
| Scope | Par requête avec continuité intelligente | ✅ |
| Router Phase 2 | Keywords/règles simples | ✅ |
| Router Phase 3 | LLM (Qwen local ou API) | 🔜 |
| Contexte | Dernier message utilisateur | ✅ |
| Intégration | Provider custom OpenClaw | ✅ |
| Support tools | Détection + routing spécialisé | ✅ |

## Catégories de routing (Phase 2)

| Catégorie | Détection | Modèles |
|-----------|-----------|---------|
| **tools** | `request.tools` présent | aurora-alpha → kimi-k2.5 → glm-5 |
| **code** | keywords: python, function, debug, api... | glm-5 → aurora-alpha → gpt-4o-mini |
| **reasoning** | keywords: why, how, explain, analyze... | aurora-alpha → glm-5 → kimi-k2.5 |
| **conversation** | messages courts, hello, thanks... | glm-5 → gpt-4o-mini → aurora-alpha |

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

## Prochaines étapes

1. Implémenter circuit breaker (marquer provider unhealthy après N échecs)
2. Ajouter métriques de coût estimé
3. Phase 3: Router LLM-based avec Qwen local
4. Tests de charge
