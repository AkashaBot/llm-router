# LLM Router

> Service de routage intelligent pour les requêtes LLM. Choix automatique du meilleur modèle selon le type de tâche.

## Démarrage rapide

```bash
cd service
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec votre OPENROUTER_API_KEY
uvicorn main:app --host 0.0.0.0 --port 3456
```

## Documentation

| Document | Description |
|----------|-------------|
| [**service/README.md**](service/README.md) | Guide d'utilisation et configuration pratique |
| [**docs/CONFIGURATION.md**](docs/CONFIGURATION.md) | Configuration détaillée (modèles, routing, etc.) |
| [**docs/API.md**](docs/API.md) | Référence API REST |
| [**docs/DEPLOYMENT.md**](docs/DEPLOYMENT.md) | Déploiement et maintenance |

## Fonctionnalités

- **Routing intelligent** via Ollama local ou API
- **Circuit breaker** avec persistence
- **Métriques de coût** en temps réel
- **Catégories personnalisables** via API
- **Support multimodal** (text, images)

## État du projet

| Phase | Status |
|-------|--------|
| Phase 1: Forward-only | ✅ |
| Phase 2: Keywords routing | ✅ |
| Phase 3: LLM-based routing | ✅ |

---

**Repo:** https://github.com/AkashaBot/llm-router
