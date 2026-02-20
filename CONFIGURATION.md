# LLM Router - Guide de Configuration

## Configuration complète

### Fichier `.env`

```bash
# === PROVIDER CIBLE ===
OPENROUTER_API_KEY=sk-or-v1-votre-cle-api

# === MODE DE ROUTING ===
# ollama: Utilise Ollama local uniquement
# api: Utilise OpenRouter API uniquement
# hybrid: Ollama avec fallback API (recommandé)
# keywords: Mode Phase 2 uniquement (fallback ultime)
ROUTING_MODE=hybrid

# === ROUTING LLM (Ollama) ===
OLLAMA_BASE_URL=http://192.168.1.168:11434
OLLAMA_ROUTER_MODEL=qwen2.5:0.5b

# === ROUTING LLM (API fallback) ===
ROUTER_API_MODEL=qwen/qwen3-1.7b

# === MODÈLE PAR DÉFAUT ===
DEFAULT_MODEL=z-ai/glm-5
```

---

## Modifier les modèles par catégorie

### Via API REST

```bash
# Modifier les modèles d'une catégorie existante
curl -X POST http://localhost:3456/config/model-mapping \
  -H "Content-Type: application/json" \
  -d '{
    "category": "code",
    "models": ["z-ai/glm-5", "moonshotai/kimi-k2.5", "openai/gpt-4o-mini"]
  }'
```

### Via fichier de configuration

Éditer `service/router_config.json`:

```json
{
  "model_mappings": {
    "tools": ["moonshotai/kimi-k2.5", "z-ai/glm-5", "openai/gpt-4o-mini"],
    "code": ["z-ai/glm-5", "openai/gpt-4o-mini", "moonshotai/kimi-k2.5"],
    "reasoning": ["moonshotai/kimi-k2.5", "z-ai/glm-5", "openai/gpt-4o-mini"],
    "conversation": ["z-ai/glm-5", "openai/gpt-4o-mini", "moonshotai/kimi-k2.5"]
  }
}
```

**Note:** Le premier modèle de la liste est le primaire, les suivants sont des fallbacks.

---

## Créer une nouvelle catégorie

### Via API REST

```bash
curl -X POST http://localhost:3456/config/category \
  -H "Content-Type: application/json" \
  -d '{
    "name": "creative",
    "models": ["moonshotai/kimi-k2.5", "z-ai/glm-5"],
    "keywords": ["story", "poem", "creative", "fiction", "write"],
    "description": "Creative writing tasks"
  }'
```

### Paramètres

| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| `name` | string | ✅ | Nom de la catégorie |
| `models` | array | ✅ | Liste des modèles (fallback chain) |
| `keywords` | array | ❌ | Keywords pour détection Phase 2 |
| `description` | string | ❌ | Description de la catégorie |

---

## Modifier le modèle de routing

### Option 1: Ollama local (recommandé)

```bash
# Dans .env
ROUTING_MODE=ollama
OLLAMA_BASE_URL=http://votre-serveur:11434
OLLAMA_ROUTER_MODEL=qwen2.5:0.5b
```

Modèles recommandés:
- `qwen2.5:0.5b` (398MB, rapide)
- `qwen2.5:1.5b` (900MB, plus précis)
- `phi-3-mini` (2GB, très précis)

### Option 2: API (OpenRouter)

```bash
# Dans .env
ROUTING_MODE=api
ROUTER_API_MODEL=qwen/qwen3-1.7b
```

Modèles légers recommandés:
- `qwen/qwen3-1.7b`
- `google/gemma-3-4b-it`
- `meta-llama/llama-3.2-1b-instruct`

### Option 3: Hybride (recommandé)

```bash
ROUTING_MODE=hybrid
# Essaie Ollama d'abord, fallback API si échec
```

---

## Logs

### Logs console (stdout)

```bash
# Démarrer avec logs visibles
cd service
python -m uvicorn main:app --host 0.0.0.0 --port 3456
```

Exemple de sortie:
```
LLM Router v0.4.0 started
Routing mode: hybrid
Ollama: http://192.168.1.168:11434 (qwen2.5:0.5b)
Categories: ['tools', 'code', 'reasoning', 'conversation', 'creative']
Request: model=router, messages=5, tools=0
INFO: POST /chat/completions HTTP/1.1" 200 OK
Circuit OPEN for moonshotai/kimi-k2.5 (failures: 3)
```

### Logs d'erreurs de validation

Fichier: `service/validation_errors.log`

Contient les erreurs de validation FastAPI détaillées.

### État du circuit breaker

Fichier: `service/circuit_breaker_state.json`

```json
{
  "failures": {"moonshotai/kimi-k2.5": 3},
  "last_failure": {"moonshotai/kimi-k2.5": 1771563500.123},
  "open_circuits": {"moonshotai/kimi-k2.5": true},
  "updated_at": "2026-02-20T07:00:00.000Z"
}
```

---

## Métriques

### Endpoint `/metrics`

```bash
curl http://localhost:3456/metrics
```

**Format de sortie:**

```json
{
  "requests": {
    "total": 1234,
    "success": 1200,
    "failed": 34
  },
  "avg_latency_ms": 1234.56,
  "total_cost_usd": 0.45,
  "model_distribution": {
    "z-ai/glm-5": 500,
    "moonshotai/kimi-k2.5": 400
  },
  "category_distribution": {
    "code": 600,
    "conversation": 400,
    "tools": 234
  },
  "routing_mode_distribution": {
    "ollama": 800,
    "api": 200,
    "keywords": 234
  },
  "circuit_breaker": {
    "failures": {"moonshotai/kimi-k2.5": 0},
    "open_circuits": {},
    "last_failure": {},
    "config": {
      "failure_threshold": 3,
      "recovery_timeout_sec": 300
    }
  },
  "config": {
    "routing_mode": "hybrid",
    "ollama_url": "http://192.168.1.168:11434",
    "ollama_model": "qwen2.5:0.5b",
    "categories": ["tools", "code", "reasoning", "conversation", "creative"]
  },
  "recent_requests": [
    {
      "timestamp": "2026-02-20T07:30:00.000Z",
      "category": "code",
      "model": "z-ai/glm-5",
      "latency_ms": 1234.56,
      "success": true,
      "routing_mode": "ollama",
      "cost_usd": 0.000123
    }
  ]
}
```

### Interprétation des métriques

| Métrique | Signification | Action si élevé |
|----------|---------------|-----------------|
| `failed` / `total` | Taux d'erreur | Vérifier circuit breaker |
| `avg_latency_ms` | Temps de réponse moyen | Optimiser routing |
| `total_cost_usd` | Coût cumulé | Surveiller budget |
| `open_circuits` | Modèles désactivés | Reset manuel si besoin |

---

## Circuit Breaker

### Fonctionnement

| État | Description | Seuil |
|------|-------------|-------|
| CLOSED | Fonctionnement normal | - |
| OPEN | Modèle désactivé | 3 erreurs consécutives |
| HALF-OPEN | Test après timeout | 5 minutes |

### Gérer le circuit breaker

```bash
# Voir l'état
curl http://localhost:3456/metrics | jq .circuit_breaker

# Reset un modèle spécifique
curl -X POST http://localhost:3456/circuit-breaker/reset/moonshotai/kimi-k2.5

# Reset tous les modèles
curl -X POST http://localhost:3456/circuit-breaker/reset-all
```

---

## Endpoints API complets

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Métriques complètes |
| GET | `/config` | Configuration actuelle |
| POST | `/config/category` | Créer/modifier une catégorie |
| POST | `/config/model-mapping` | Modifier modèles d'une catégorie |
| DELETE | `/config/category/{name}` | Supprimer une catégorie |
| POST | `/circuit-breaker/reset/{model}` | Reset un modèle |
| POST | `/circuit-breaker/reset-all` | Reset tous les modèles |
| POST | `/v1/chat/completions` | OpenAI-compatible |
| POST | `/chat/completions` | Alias OpenClaw |

---

## Intégration OpenClaw

Dans `~/.openclaw/openclaw.json`:

```json
{
  "models": {
    "providers": {
      "router": {
        "baseUrl": "http://localhost:3456",
        "apiKey": "local-router",
        "api": "openai-completions",
        "models": [{ "id": "router" }]
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

---

## Dépannage

### Le router ne démarre pas

```bash
# Vérifier les dépendances
pip install -r requirements.txt

# Vérifier le port
netstat -an | findstr 3456

# Vérifier la config
cat service/.env
```

### Erreurs 422

Causes possibles:
- `content` au mauvais format → fixé avec `content: Any`
- Requête trop volumineuse → réduire le contexte

### Erreurs 500 / Circuit breaker ouvert

```bash
# Reset le circuit breaker
curl -X POST http://localhost:3456/circuit-breaker/reset-all

# Ou redémarrer le service (reset automatique au démarrage)
```

### Ollama non accessible

```bash
# Vérifier la connexion
curl http://192.168.1.168:11434/api/tags

# Changer pour mode API fallback
ROUTING_MODE=api
```
