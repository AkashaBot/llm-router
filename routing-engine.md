# Routing Engine

## Fonction

Le moteur de décision qui détermine quel modèle LLM utiliser pour chaque requête.

## Phase 3: Routing LLM-based (implémenté)

### Modes disponibles

| Mode | Description | Utilisation |
|------|-------------|-------------|
| `ollama` | Routing via Ollama local | Priorité performances |
| `api` | Routing via API OpenRouter | Fallback réseau |
| `hybrid` | Ollama + fallback API | **Recommandé** |
| `keywords` | Phase 2 uniquement | Fallback ultime |

### Flux de routing

```
Requête entrante
       │
       ├── has_tools? → catégorie "tools" (direct)
       │
       ├── is_continuation? → garde modèle précédent
       │
       ├── ROUTING_MODE in ["ollama", "hybrid"]
       │         │
       │         ├── Ollama disponible? → route_with_ollama()
       │         │         │
       │         │         └── Catégorie détectée
       │         │
       │         └── ROUTING_MODE == "hybrid"?
       │                   │
       │                   └── API fallback → route_with_api()
       │
       └── Fallback: keywords (Phase 2)
```

### Prompt de routing

```
Tu es un routeur de modèles LLM. Analyse la requête et choisis la meilleure catégorie.

Catégories disponibles: tools, code, reasoning, conversation, creative, ...

Règles:
- tools: si la requête nécessite des appels de fonction/outils
- code: pour écrire, corriger, expliquer du code
- reasoning: pour analyser, raisonner, expliquer un concept complexe
- conversation: pour les discussions simples, questions rapides
- custom: autres catégories définies par l'utilisateur

Requête: {message}

Catégorie:
```

### Configuration Ollama

```python
OLLAMA_BASE_URL = "http://192.168.1.168:11434"
OLLAMA_ROUTER_MODEL = "qwen2.5:0.5b"
```

Le modèle qwen2.5:0.5b (398MB) offre un bon compromis:
- Latence: ~5-15s (premier appel avec load)
- Précision: ~90% sur les cas standards
- Coût: 0 (local)

### Fallback keywords (Phase 2)

Si Ollama/API indisponible, détection par keywords:

```python
KEYWORDS = {
    "code": ["python", "function", "debug", "api", ...],
    "reasoning": ["why", "how", "explain", "analyze", ...],
    "conversation": ["hello", "thanks", "yes", "no", ...],
    # + catégories personnalisées
}
```

### Continuité de session

Pour éviter de re-router à chaque message:

```python
SHORT_CONTINUATION = [
    r"^ok$", r"^okay$", r"^yes$", r"^no$",
    r"^thanks?$", r"^please$", r"^sure$",
    r"^[a-zA-Z]{1,3}$"  # Messages très courts
]

# Si message court → garde le modèle précédent
```

## Catégories personnalisées

Ajout via API:

```bash
POST /config/category
{
  "name": "creative",
  "models": ["aurora-alpha", "glm-5"],
  "keywords": ["story", "poem", "creative"],
  "description": "Creative writing tasks"
}
```

Le routing LLM prend automatiquement en compte les nouvelles catégories.
