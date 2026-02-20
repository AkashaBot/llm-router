# Déploiement

## Démarrage

```bash
cd service
uvicorn main:app --host 0.0.0.0 --port 3456
```

## Auto-start

### Linux/macOS (systemd)

Créer `/etc/systemd/system/llm-router.service`:

```ini
[Unit]
Description=LLM Router
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/llm-router/service
ExecStart=/path/to/venv/bin/uvicorn main:app --host 0.0.0.0 --port 3456
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable llm-router
sudo systemctl start llm-router
```

### Linux/macOS (crontab)

```bash
crontab -e
# Ajouter:
@reboot cd /path/to/llm-router/service && uvicorn main:app --host 0.0.0.0 --port 3456
```

### Windows (Task Scheduler)

1. Ouvrir "Task Scheduler"
2. Créer tâche "LLM Router"
3. Déclencheur: "At startup"
4. Action: `python -m uvicorn main:app --host 0.0.0.0 --port 3456`
5. Répertoire: `C:\path\to\llm-router\service`

### Docker

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY service/requirements.txt .
RUN pip install -r requirements.txt
COPY service/ .
EXPOSE 3456
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3456"]
```

```bash
docker build -t llm-router .
docker run -p 3456:3456 --env-file .env llm-router
```

---

## Configuration production

### Variables recommandées

```bash
ROUTING_MODE=hybrid
OPENROUTER_API_KEY=sk-or-v1-...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Ports

| Service | Port |
|---------|------|
| LLM Router | 3456 |
| Ollama | 11434 |

### Firewall

```bash
# Linux (ufw)
sudo ufw allow 3456/tcp

# Linux (iptables)
sudo iptables -A INPUT -p tcp --dport 3456 -j ACCEPT

# Windows
netsh advfirewall firewall add rule name="LLM Router" dir=in action=allow protocol=tcp localport=3456
```

---

## Monitoring

```bash
curl http://localhost:3456/health
curl http://localhost:3456/metrics
```

---

## Troubleshooting

### Port occupé

```bash
# Linux/macOS
lsof -i :3456
kill -9 <PID>

# Windows
netstat -an | findstr 3456
taskkill /PID <PID> /F
```

### Provider non configuré

```bash
# Vérifier la configuration
curl http://localhost:3456/providers
```

### Circuit breaker ouvert

```bash
curl -X POST http://localhost:3456/circuit-breaker/reset-all
```

### Logs

Surveiller la sortie console ou rediriger:

```bash
uvicorn main:app --host 0.0.0.0 --port 3456 >> router.log 2>&1
```
