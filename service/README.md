# LLM Router Service

Service FastAPI de routage intelligent pour les requêtes LLM.

## Fonctionnalités

- **Routing automatique** par détection de catégorie (code/reasoning/conversation/tools)
- **Support function calling** - détection des requêtes avec tools et routing spécialisé
- **Fallback chain** - basculement automatique vers modèles alternatifs si échec
- **Monitoring** - endpoint `/metrics` avec latence, distribution modèles, succès/échec
- **OpenAI-compatible** - endpoint `/v1/chat/completions` compatible OpenAI

## Installation

```bash
# Créer l'environnement virtuel
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Installer les dépendances
pip install -r requirements.txt

# Configurer
cp .env.example .env
# Éditer .env avec votre OPENROUTER_API_KEY
```

## Démarrage

```bash
uvicorn main:app --host 0.0.0.0 --port 3456
```

## Endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/v1/chat/completions` | Chat completions (OpenAI-compatible) |
| POST | `/chat/completions` | Alias pour compatibilité OpenClaw |
| GET | `/health` | Health check |
| GET | `/metrics` | Métriques d'utilisation |
| GET | `/models` | Liste des modèles disponibles |

## Routing

| Catégorie | Détection | Modèles |
|-----------|-----------|---------|
| tools | `request.tools` présent | aurora-alpha → kimi-k2.5 → glm-5 |
| code | keywords: python, function... | glm-5 → aurora-alpha → gpt-4o-mini |
| reasoning | keywords: why, how, explain... | aurora-alpha → glm-5 → kimi-k2.5 |
| conversation | messages courts | glm-5 → gpt-4o-mini → aurora-alpha |

## Configuration

Variables d'environnement (`.env`):

```
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
PHASE2_ENABLED=true
```

## Exemple d'utilisation

```bash
# Test simple
curl -X POST http://localhost:3456/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"router","messages":[{"role":"user","content":"Hello!"}]}'

# Test avec tools
curl -X POST http://localhost:3456/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model":"router",
    "messages":[{"role":"user","content":"What is the weather?"}],
    "tools":[{"type":"function","function":{"name":"get_weather"}}]
  }'

# Métriques
curl http://localhost:3456/metrics
```

## Intégration OpenClaw

Voir `../README.md` pour la configuration complète.
