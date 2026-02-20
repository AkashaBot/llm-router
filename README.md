# LLM Router

> Service de routage intelligent multi-provider pour les requêtes LLM.

## Démarrage rapide

```bash
cd service
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec vos clés API
uvicorn main:app --host 0.0.0.0 --port 3456
```

## Documentation

| Document | Description |
|----------|-------------|
| [**service/README.md**](service/README.md) | Guide d'utilisation |
| [**docs/CONFIGURATION.md**](docs/CONFIGURATION.md) | Configuration détaillée |
| [**docs/API.md**](docs/API.md) | Référence API REST |
| [**docs/DEPLOYMENT.md**](docs/DEPLOYMENT.md) | Déploiement |

## Providers supportés

| Provider | Clé API requise | Coût |
|----------|-----------------|------|
| **OpenRouter** | `OPENROUTER_API_KEY` | Payant (varié) |
| **OpenAI** | `OPENAI_API_KEY` | Payant |
| **Anthropic** | `ANTHROPIC_API_KEY` | Payant |
| **Google** | `GOOGLE_API_KEY` | Payant |
| **Ollama** | Aucune | Gratuit (local) |

## Fonctionnalités

- ✅ **Multi-provider** - Mixez OpenRouter, OpenAI, Anthropic, Google, Ollama
- ✅ **Routing intelligent** via Ollama local ou API
- ✅ **Circuit breaker** persistant
- ✅ **Métriques de coût** temps réel
- ✅ **Catégories personnalisables**

## Version

**v0.5.0** - Multi-provider support

---

**Repo:** https://github.com/AkashaBot/llm-router
