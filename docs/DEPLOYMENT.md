# Déploiement

## Démarrage manuel

```bash
cd service
uvicorn main:app --host 0.0.0.0 --port 3456
```

## Auto-start (Windows)

### Option 1: Tâche planifiée Windows

1. Ouvrir "Planificateur de tâches"
2. Créer une tâche "LLM Router"
3. Déclencheur: "Au démarrage"
4. Action: `python -m uvicorn main:app --host 0.0.0.0 --port 3456`
5. Répertoire: `C:\Users\algon\clawd\plans\llm-router\service`

### Option 2: Script de démarrage

Créer `start_router.bat`:

```batch
@echo off
cd C:\Users\algon\clawd\plans\llm-router\service
python -m uvicorn main:app --host 0.0.0.0 --port 3456
```

Placer dans le dossier de démarrage Windows:
```
shell:startup
```

---

## Production

### Variables recommandées

```bash
ROUTING_MODE=hybrid
OPENROUTER_API_KEY=sk-or-v1-...
OLLAMA_BASE_URL=http://192.168.1.168:11434
```

### Ports

| Service | Port |
|---------|------|
| LLM Router | 3456 |
| Ollama | 11434 |

### Firewall

Ouvrir le port 3456 si accès distant:
```bash
netsh advfirewall firewall add rule name="LLM Router" dir=in action=allow protocol=tcp localport=3456
```

---

## Monitoring

### Health check

```bash
curl http://localhost:3456/health
```

### Métriques

```bash
curl http://localhost:3456/metrics | jq
```

---

## Maintenance

### Logs

Surveiller la console pour les erreurs.

### Circuit breaker

Vérifier régulièrement:
```bash
curl http://localhost:3456/metrics | jq .circuit_breaker
```

### Reset complet

```bash
# Reset circuit breaker
curl -X POST http://localhost:3456/circuit-breaker/reset-all

# Redémarrer le service
# (kill process + restart)
```

---

## Troubleshooting

### Port déjà utilisé

```bash
netstat -an | findstr 3456
# Kill le process trouvé
```

### Erreurs 422 en boucle

1. Vérifier `validation_errors.log`
2. Vérifier le format des requêtes
3. Redémarrer le service

### Tous les modèles désactivés

```bash
curl -X POST http://localhost:3456/circuit-breaker/reset-all
```

### Ollama non joignable

1. Vérifier l'URL: `curl http://192.168.1.168:11434/api/tags`
2. Utiliser `ROUTING_MODE=api` en fallback
