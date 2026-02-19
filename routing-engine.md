# Routing Engine

## Fonction

Le moteur de décision qui détermine quel modèle LLM utiliser pour chaque requête.

## Phase 2: Routing par Keywords (implémenté)

### Détection par catégorie

```python
CODE_KEYWORDS = ["python", "function", "code", "debug", "api", "git", "refactor", ...]
REASONING_KEYWORDS = ["why", "how", "explain", "analyze", "think", "prove", ...]
CONVERSATION_KEYWORDS = ["hello", "thanks", "yes", "no", "ok", "sure", ...]

def detect_category(message: str) -> str:
    message_lower = message.lower()
    for keyword in CODE_KEYWORDS:
        if keyword in message_lower:
            return "code"
    for keyword in REASONING_KEYWORDS:
        if keyword in message_lower:
            return "reasoning"
    if len(message.split()) < 5:
        return "conversation"
    return "conversation"
```

### Détection tools

```python
if request.tools is not None and len(request.tools) > 0:
    category = "tools"
    models = MODEL_MAPPINGS["tools"]
```

### Continuité de session

Pour éviter de re-router à chaque message:
- Messages courts (< 5 mots) → garder le même modèle
- Stockage de la décision précédente par `session_id`

```python
# Session state: {session_id: {"last_model": "...", "last_category": "..."}}
if is_short_message(message) and session_state.get("last_model"):
    return session_state["last_model"]
```

## Phase 3: Router LLM-based (à venir)

Utilisation d'un petit modèle (Qwen-0.5B) pour le routing intelligent.

### Prompt de routing (draft)

```
Tu es un router de modèles LLM. Analyse cette requête et décide quel modèle utiliser.

Contexte récent (3 derniers échanges):
{context}

Requête actuelle: {user_message}

Types disponibles:
- code: Pour le code, debug, refactoring, fichiers techniques
- reasoning: Pour l'analyse, la réflexion, les problèmes complexes
- conversation: Pour les questions simples, le small talk, les réponses rapides
- tools: Pour les requêtes avec function calling

Réponds uniquement avec un mot: code, reasoning, conversation, ou tools
```

## Avantages Phase 2 vs Phase 3

| Aspect | Phase 2 (Keywords) | Phase 3 (LLM) |
|--------|-------------------|---------------|
| Latence | ~0ms | ~100-500ms |
| Précision | Bonne pour cas simples | Meilleure pour cas ambigus |
| Maintenance | Keywords à maintenir | Prompt à ajuster |
| Coût | 0 | Légèrement plus élevé |
