# Configuration détaillée

## Variables d'environnement

### Fichier `.env`

```bash
# === PROVIDER CIBLE ===
OPENROUTER_API_KEY=sk-or-v1-votre-cle

# === MODE DE ROUTING ===
# ollama: Ollama local uniquement
# api: OpenRouter API uniquement  
# hybrid: Ollama + fallback API (recommandé)
# keywords: Fallback Phase 2
ROUTING_MODE=hybrid

# === ROUTING OLLAMA ===
OLLAMA_BASE_URL=http://192.168.1.168:11434
OLLAMA_ROUTER_MODEL=qwen2.5:0.5b

# === ROUTING API ===
ROUTER_API_MODEL=qwen/qwen3-1.7b
```

---

## Routing LLM

### Mode Ollama (local)

Avantages: Gratuit, privé, rapide  
Inconvénients: Nécessite un serveur Ollama

```bash
ROUTING_MODE=ollama
OLLAMA_BASE_URL=http://votre-serveur:11434
OLLAMA_ROUTER_MODEL=qwen2.5:0.5b
```

Modèles recommandés:
- `qwen2.5:0.5b` (398MB) - Rapide
- `qwen2.5:1.5b` (900MB) - Équilibré
- `phi-3-mini` (2GB) - Précis

### Mode API

Avantages: Simple, pas d'infrastructure  
Inconvénients: Coût, latence réseau

```bash
ROUTING_MODE=api
ROUTER_API_MODEL=qwen/qwen3-1.7b
```

Modèles légers sur OpenRouter:
- `qwen/qwen3-1.7b` (~$0.01/1M input)
- `google/gemma-3-4b-it`
- `meta-llama/llama-3.2-1b-instruct`

### Mode Hybride (recommandé)

Essaie Ollama, fallback API si échec.

```bash
ROUTING_MODE=hybrid
```

---

## Modèles par catégorie

### Via API

```bash
curl -X POST http://localhost:3456/config/model-mapping \
  -H "Content-Type: application/json" \
  -d '{"category": "code", "models": ["glm-5", "kimi-k2.5", "gpt-4o-mini"]}'
```

### Via fichier

Éditer `router_config.json`:

```json
{
  "model_mappings": {
    "tools": ["moonshotai/kimi-k2.5", "z-ai/glm-5", "openai/gpt-4o-mini"],
    "code": ["z-ai/glm-5", "openai/gpt-4o-mini", "moonshotai/kimi-k2.5"]
  }
}
```

**Format:** Premier modèle = primaire, suivants = fallbacks.

---

## Catégories personnalisées

### Créer une catégorie

```bash
curl -X POST http://localhost:3456/config/category \
  -H "Content-Type: application/json" \
  -d '{
    "name": "creative",
    "models": ["moonshotai/kimi-k2.5"],
    "keywords": ["story", "poem", "creative"],
    "description": "Creative writing"
  }'
```

### Supprimer une catégorie

```bash
curl -X DELETE http://localhost:3456/config/category/creative
```

---

## Circuit Breaker

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| `failure_threshold` | 3 | Erreurs avant désactivation |
| `recovery_timeout_sec` | 300 | Secondes avant retry |

L'état est persisté dans `circuit_breaker_state.json`.

---

## Coûts OpenRouter

*Source: [openrouter.ai/models](https://openrouter.ai/models)*

| Modèle | Input ($/1M) | Output ($/1M) | Notes |
|--------|--------------|---------------|-------|
| kimi-k2.5 | 0.60 | 3.00 | Multimodal, excellent pour tools |
| glm-5 | 0.05 | 0.15 | Très économique, bon généraliste |
| gpt-4o-mini | 0.15 | 0.60 | OpenAI, fiable |
| qwen3-1.7b | 0.01 | 0.02 | Ultra-économique, pour routing |

---

## Logs

| Fichier | Contenu |
|---------|---------|
| Console | Requêtes, erreurs, circuit breaker |
| `validation_errors.log` | Erreurs de validation détaillées |
| `circuit_breaker_state.json` | État persisté du CB |
