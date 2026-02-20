# Guide d'utilisation

## Installation

```bash
cd service
pip install -r requirements.txt
cp .env.example .env
```

## Configuration minimale

Éditer `.env`:

```bash
OPENROUTER_API_KEY=sk-or-v1-votre-cle
```

## Démarrage

```bash
uvicorn main:app --host 0.0.0.0 --port 3456
```

## Vérification

```bash
curl http://localhost:3456/health
```

---

## Modèles utilisés

| Catégorie | Modèles (fallback chain) |
|-----------|--------------------------|
| **tools** | kimi-k2.5 → glm-5 → gpt-4o-mini |
| **code** | glm-5 → gpt-4o-mini → kimi-k2.5 |
| **reasoning** | kimi-k2.5 → glm-5 → gpt-4o-mini |
| **conversation** | glm-5 → gpt-4o-mini → kimi-k2.5 |

### Coûts estimés (OpenRouter)

| Modèle | Input | Output |
|--------|-------|--------|
| kimi-k2.5 | $0.60/1M | $3.00/1M |
| glm-5 | $0.05/1M | $0.15/1M |
| gpt-4o-mini | $0.15/1M | $0.60/1M |

*Source: [OpenRouter](https://openrouter.ai/models)*

---

## Endpoints principaux

```bash
# Requête chat
POST /v1/chat/completions
POST /chat/completions  # Alias OpenClaw

# Monitoring
GET /health
GET /metrics

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

### Changer les modèles d'une catégorie

```bash
curl -X POST http://localhost:3456/config/model-mapping \
  -H "Content-Type: application/json" \
  -d '{"category": "code", "models": ["glm-5", "kimi-k2.5"]}'
```

### Créer une nouvelle catégorie

```bash
curl -X POST http://localhost:3456/config/category \
  -H "Content-Type: application/json" \
  -d '{
    "name": "creative",
    "models": ["kimi-k2.5", "glm-5"],
    "keywords": ["story", "poem", "creative"]
  }'
```

---

## Métriques

```bash
curl http://localhost:3456/metrics | jq
```

Sortie:
```json
{
  "requests": {"total": 100, "success": 98, "failed": 2},
  "avg_latency_ms": 1234,
  "total_cost_usd": 0.45,
  "circuit_breaker": {"open_circuits": {}}
}
```

---

## Circuit Breaker

Le circuit breaker désactive automatiquement un modèle après 3 erreurs consécutives.

```bash
# Voir l'état
curl http://localhost:3456/metrics | jq .circuit_breaker

# Reset un modèle
curl -X POST http://localhost:3456/circuit-breaker/reset/kimi-k2.5

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
| `.env` | Configuration (API keys, routing mode) |
| `router_config.json` | Modèles et catégories sauvegardés |
| `circuit_breaker_state.json` | État du circuit breaker |
| `validation_errors.log` | Erreurs de validation détaillées |

---

## Dépannage

| Problème | Solution |
|----------|----------|
| Port 3456 occupé | `netstat -an \| findstr 3456` puis kill |
| 422 Validation error | Voir `validation_errors.log` |
| Circuit breaker ouvert | Reset via API |
| Ollama non accessible | Vérifier `OLLAMA_BASE_URL` ou utiliser `ROUTING_MODE=api` |
