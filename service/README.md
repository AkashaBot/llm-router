# Guide d'utilisation

## Installation

```bash
# Créer un environnement virtuel (optionnel mais recommandé)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer
cp .env.example .env
```

## Configuration minimale

Éditer `.env` avec au moins un provider:

```bash
# Option 1: OpenRouter (recommandé, accès à tous les modèles)
OPENROUTER_API_KEY=sk-or-v1-votre-cle

# Option 2: OpenAI direct
OPENAI_API_KEY=sk-votre-cle-openai

# Option 3: Anthropic
ANTHROPIC_API_KEY=sk-ant-votre-cle

# Option 4: Google
GOOGLE_API_KEY=votre-cle-google

# Option 5: Ollama local (gratuit)
OLLAMA_BASE_URL=http://localhost:11434
```

## Démarrage

```bash
uvicorn main:app --host 0.0.0.0 --port 3456
```

Vérifier: `curl http://localhost:3456/health`

---

## Multi-provider

### Format des IDs de modèle

Les modèles sont identifiés par `provider/model`:

```
openrouter/moonshotai/kimi-k2.5
openai/gpt-4o
anthropic/claude-3-opus
google/gemini-1.5-pro
ollama/llama3.1
```

### Configuration par défaut

| Catégorie | Modèles (fallback chain) |
|-----------|--------------------------|
| **tools** | openrouter/kimi-k2.5 → openrouter/glm-5 → openai/gpt-4o-mini |
| **code** | openrouter/glm-5 → openai/gpt-4o-mini → openrouter/kimi-k2.5 |
| **reasoning** | openrouter/kimi-k2.5 → openrouter/glm-5 → openai/gpt-4o-mini |
| **conversation** | openrouter/glm-5 → openai/gpt-4o-mini → openrouter/kimi-k2.5 |

### Mix providers

Vous pouvez mixer les providers dans une même catégorie:

```bash
curl -X POST http://localhost:3456/config/model-mapping \
  -H "Content-Type: application/json" \
  -d '{
    "category": "tools",
    "models": [
      "openrouter/moonshotai/kimi-k2.5",
      "openai/gpt-4o",
      "anthropic/claude-3-sonnet"
    ]
  }'
```

---

## Coûts estimés

*Source: OpenRouter, OpenAI, Anthropic (février 2026)*

| Modèle | Input ($/1M) | Output ($/1M) | Provider |
|--------|--------------|---------------|----------|
| kimi-k2.5 | 0.60 | 3.00 | OpenRouter |
| glm-5 | 0.05 | 0.15 | OpenRouter |
| gpt-4o | 2.50 | 10.00 | OpenAI |
| gpt-4o-mini | 0.15 | 0.60 | OpenAI |
| claude-3-opus | 15.00 | 75.00 | Anthropic |
| claude-3-sonnet | 3.00 | 15.00 | Anthropic |
| gemini-1.5-pro | 1.25 | 5.00 | Google |
| llama3.1 | 0 | 0 | Ollama |

---

## Endpoints

```bash
# Chat
POST /v1/chat/completions
POST /chat/completions

# Monitoring
GET /health
GET /metrics
GET /providers

# Configuration
GET /config
POST /config/category
POST /config/model-mapping
DELETE /config/category/{name}

# Circuit breaker
POST /circuit-breaker/reset/{model}
POST /circuit-breaker/reset-all
```

---

## Modifier les modèles

### Via API

```bash
# Changer les modèles d'une catégorie
curl -X POST http://localhost:3456/config/model-mapping \
  -H "Content-Type: application/json" \
  -d '{"category": "code", "models": ["openai/gpt-4o", "anthropic/claude-3-sonnet"]}'

# Créer une catégorie
curl -X POST http://localhost:3456/config/category \
  -H "Content-Type: application/json" \
  -d '{"name": "creative", "models": ["openrouter/kimi-k2.5"], "keywords": ["story", "poem"]}'
```

### Via fichier

Éditer `router_config.json`:

```json
{
  "model_mappings": {
    "tools": ["openrouter/kimi-k2.5", "openai/gpt-4o"],
    "code": ["openrouter/glm-5", "anthropic/claude-3-sonnet"]
  }
}
```

---

## Métriques

```bash
curl http://localhost:3456/metrics
```

```json
{
  "requests": {"total": 100, "success": 98, "failed": 2},
  "avg_latency_ms": 1234,
  "total_cost_usd": 0.45,
  "provider_distribution": {
    "openrouter": 60,
    "openai": 30,
    "anthropic": 10
  },
  "circuit_breaker": {"open_circuits": {}}
}
```

---

## Circuit Breaker

Désactive un modèle après 3 erreurs consécutives, réessaie après 5 min.

```bash
# État
curl http://localhost:3456/metrics | jq .circuit_breaker

# Reset un modèle
curl -X POST http://localhost:3456/circuit-breaker/reset/openai/gpt-4o

# Reset tous
curl -X POST http://localhost:3456/circuit-breaker/reset-all
```

---

## Intégration OpenClaw

Dans `~/.openclaw/openclaw.json`:

```json
{
  "models": {
    "providers": {
      "router": {
        "baseUrl": "http://localhost:3456",
        "api": "openai-completions",
        "models": [{"id": "router"}]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {"primary": "router/router"}
    }
  }
}
```

---

## Fichiers

| Fichier | Description |
|---------|-------------|
| `.env` | Clés API et configuration |
| `router_config.json` | Modèles et catégories |
| `circuit_breaker_state.json` | État du circuit breaker |
| `validation_errors.log` | Erreurs détaillées |

---

## Dépannage

| Problème | Solution |
|----------|----------|
| Port 3456 occupé | `lsof -i :3456` (Linux/Mac) ou `netstat -an \| findstr 3456` (Windows) |
| Provider non configuré | Ajouter la clé API dans `.env` |
| Circuit breaker ouvert | `POST /circuit-breaker/reset-all` |
| Ollama non joignable | Vérifier `OLLAMA_BASE_URL` |
