# Déploiement

## Scripts fournis

| Script | OS | Usage |
|--------|-----|-------|
| `scripts/start.sh` | Linux/macOS | Démarrage manuel |
| `scripts/start.bat` | Windows | Démarrage manuel |
| `scripts/health-check.sh` | Linux/macOS | Vérification + restart auto |
| `scripts/health-check.ps1` | Windows | Vérification + restart auto |

---

## Démarrage manuel

```bash
# Linux/macOS
./scripts/start.sh

# Windows
scripts\start.bat

# Ou directement
cd service
uvicorn main:app --host 0.0.0.0 --port 3456
```

---

## Auto-start au boot

### Linux (systemd)

```bash
sudo nano /etc/systemd/system/llm-router.service
```

```ini
[Unit]
Description=LLM Router
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/llm-router/service
Environment="ROUTER_DIR=/path/to/llm-router/service"
ExecStart=/usr/bin/uvicorn main:app --host 0.0.0.0 --port 3456
Restart=always
RestartSec=5

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
```

```cron
# Start at boot
@reboot /path/to/llm-router/scripts/start.sh

# Health check every 5 minutes
*/5 * * * * /path/to/llm-router/scripts/health-check.sh
```

### Windows (Task Scheduler - boot)

1. Ouvrir "Task Scheduler" (taskschd.msc)
2. Create Task → "LLM Router"
3. **Trigger:** "At startup"
4. **Action:** Start a program
   - Program: `powershell`
   - Arguments: `-ExecutionPolicy Bypass -File C:\path\to\llm-router\scripts\start.bat`
5. **Settings:** "Run whether user is logged on or not"

### Windows (Task Scheduler - health check)

1. Create Task → "LLM Router Health Check"
2. **Trigger:** "On a schedule" → "Repeat every 5 minutes"
3. **Action:** Start a program
   - Program: `powershell`
   - Arguments: `-ExecutionPolicy Bypass -File C:\path\to\llm-router\scripts\health-check.ps1`

---

## Docker

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY service/requirements.txt .
RUN pip install -r requirements.txt
COPY service/ .
EXPOSE 3456
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:3456/health || exit 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3456"]
```

```bash
docker build -t llm-router .
docker run -d \
  --name llm-router \
  --restart always \
  -p 3456:3456 \
  --env-file .env \
  llm-router
```

---

## Configuration production

### Variables recommandées

```bash
ROUTING_MODE=hybrid
OPENROUTER_API_KEY=sk-or-v1-...
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

### Router ne répond pas

```bash
# Linux/macOS
./scripts/health-check.sh

# Windows
powershell -ExecutionPolicy Bypass -File scripts\health-check.ps1
```

### Circuit breaker ouvert

```bash
curl -X POST http://localhost:3456/circuit-breaker/reset-all
```

### Logs

```bash
# Les scripts écrivent dans service/health.log
tail -f service/health.log
```
