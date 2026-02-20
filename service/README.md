# LLM Router Service

Service FastAPI de routage intelligent pour les requêtes LLM.

## Fonctionnalités

- **Routing intelligent** via Ollama (qwen2.5:0.5b) ou API
- **Circuit breaker** - désactive automatiquement les modèles défaillants
- **Métriques de coût** - estimation USD par requête
- **Catégories personnalisables** - ajoutez vos propres cas d'usage
- **Support function calling** - détection automatique des tools
- **OpenAI-compatible** - endpoint `/v1/chat/completions`

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
| GET | `/config` | Configuration actuelle |
| POST | `/config/category` | Ajouter/modifier une catégorie |
| POST | `/config/model-mapping` | Modifier les modèles d'une catégorie |
| DELETE | `/config/category/{name}` | Supprimer une catégorie personnalisée |
| POST | `/circuit-breaker/reset/{model}` | Réinitialiser le circuit breaker |

## Routing

| Catégorie | Détection | Modèles |
|-----------|-----------|---------|
| tools | `request.tools` présent | aurora-alpha → kimi-k2.5 → glm-5 |
| code | keywords: python, function... | glm-5 → aurora-alpha → gpt-4o-mini |
| reasoning | keywords: why, how, explain... | aurora-alpha → glm-5 → kimi-k2.5 |
| conversation | messages courts | glm-5 → gpt-4o-mini → aurora-alpha |

## Configuration

Variables d'environnement (`.env`):

```bash
# OpenRouter API
OPENROUTER_API_KEY=sk-or-v1-...

# Routing mode: "ollama" | "api" | "hybrid" | "keywords"
ROUTING_MODE=hybrid

# Ollama config
OLLAMA_BASE_URL=http://192.168.1.168:11434
OLLAMA_ROUTER_MODEL=qwen2.5:0.5b

# API routing fallback
ROUTER_API_MODEL=qwen/qwen3-1.7b
```

## Circuit Breaker

- **Seuil**: 3 erreurs consécutives
- **Recovery**: 5 minutes
- **Reset manuel**: `POST /circuit-breaker/reset/{model}`

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

# Ajouter une catégorie
curl -X POST http://localhost:3456/config/category \
  -H "Content-Type: application/json" \
  -d '{"name":"creative","models":["aurora-alpha"],"keywords":["story","poem"]}'

# Métriques
curl http://localhost:3456/metrics
```

## Fichiers

- `main.py` - Service FastAPI principal
- `requirements.txt` - Dépendances Python
- `.env.example` - Template de configuration
- `router_config.json` - Configuration sauvegardée (généré automatiquement)
