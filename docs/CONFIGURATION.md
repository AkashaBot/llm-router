# Configuration détaillée

## Variables d'environnement

Fichier `.env`:

```bash
# === PROVIDERS ===
# Au moins un provider doit être configuré

# OpenRouter (recommandé)
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# OpenAI direct
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_BASE_URL=https://api.anthropic.com/v1

# Google
GOOGLE_API_KEY=...
GOOGLE_BASE_URL=https://generativelanguage.googleapis.com/v1beta

# Ollama (local, gratuit)
OLLAMA_BASE_URL=http://localhost:11434

# === ROUTING ===
# ollama | api | hybrid | keywords
ROUTING_MODE=hybrid
OLLAMA_ROUTER_MODEL=qwen2.5:0.5b
ROUTER_API_MODEL=openrouter/qwen/qwen3-1.7b

# === DÉFAUT ===
DEFAULT_PROVIDER=openrouter
DEFAULT_MODEL=glm-5
```

---

## Format des modèles

### Syntaxe

```
provider/model-name
```

### Exemples

```
openrouter/moonshotai/kimi-k2.5    # OpenRouter avec chemin complet
openai/gpt-4o                       # OpenAI direct
anthropic/claude-3-opus             # Anthropic
google/gemini-1.5-pro               # Google
ollama/llama3.1                     # Ollama local
```

### Provider par défaut

Si pas de préfixe, `DEFAULT_PROVIDER` est utilisé:

```bash
# Si DEFAULT_PROVIDER=openrouter
glm-5  # → openrouter/glm-5
```

---

## Routing LLM

### Mode Ollama (local)

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

```bash
ROUTING_MODE=api
ROUTER_API_MODEL=openrouter/qwen/qwen3-1.7b
```

### Mode Hybride (recommandé)

```bash
ROUTING_MODE=hybrid
# Essaie Ollama, fallback API
```

---

## Mix de providers

### Exemple: tools avec fallback multi-provider

```json
{
  "tools": [
    "openrouter/moonshotai/kimi-k2.5",
    "openai/gpt-4o",
    "anthropic/claude-3-sonnet"
  ]
}
```

Si OpenRouter échoue → OpenAI → Anthropic.

### Exemple: Utiliser Ollama en fallback

```json
{
  "conversation": [
    "openrouter/z-ai/glm-5",
    "openai/gpt-4o-mini",
    "ollama/llama3.1"
  ]
}
```

Si tous les providers payants échouent → Ollama local (gratuit).

---

## Circuit Breaker

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| `failure_threshold` | 3 | Erreurs avant désactivation |
| `recovery_timeout_sec` | 300 | Secondes avant retry |

L'état est persisté dans `circuit_breaker_state.json`.

---

## Fichier de configuration

`router_config.json`:

```json
{
  "model_mappings": {
    "tools": ["openrouter/kimi-k2.5", "openai/gpt-4o"],
    "code": ["openrouter/glm-5", "anthropic/claude-3-sonnet"],
    "reasoning": ["openrouter/kimi-k2.5", "openai/gpt-4o"],
    "conversation": ["openrouter/glm-5", "ollama/llama3.1"]
  },
  "keywords": {
    "code": ["python", "function", "debug", "git"],
    "reasoning": ["why", "how", "explain", "analyze"]
  },
  "custom_categories": {
    "creative": {
      "models": ["openrouter/kimi-k2.5"],
      "keywords": ["story", "poem"]
    }
  }
}
```

---

## Logs

| Fichier | Contenu |
|---------|---------|
| Console | Requêtes, erreurs, routing |
| `validation_errors.log` | Erreurs de validation |
| `circuit_breaker_state.json` | État persisté |
