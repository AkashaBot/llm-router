# OpenClaw Agent Integration

This guide explains how to configure and use LLM Router with OpenClaw agents.

---

## Why Use Router with OpenClaw?

| Problem | Router Solution |
|---------|-----------------|
| Agents crash when model fails | Automatic fallback to alternatives |
| Different tasks need different models | Auto-detect task type and route |
| No visibility on costs | Track USD per request |
| Tools support varies by model | Route tool requests to capable models |

---

## Quick Setup

### 1. Start Router

```bash
cd llm-router/service
uvicorn main:app --host 0.0.0.0 --port 3456
```

### 2. Configure OpenClaw

Edit `~/.openclaw/openclaw.json`:

```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "router": {
        "baseUrl": "http://localhost:3456",
        "apiKey": "local-router",
        "api": "openai-completions",
        "models": [
          {
            "id": "router",
            "name": "LLM Router",
            "reasoning": true,
            "input": ["text"],
            "cost": {
              "input": 0,
              "output": 0
            },
            "contextWindow": 200000,
            "maxTokens": 8192
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "router/router",
        "fallbacks": [
          "openrouter/z-ai/glm-5",
          "nvidia-nim/moonshotai/kimi-k2.5"
        ]
      }
    }
  }
}
```

### 3. Restart OpenClaw

```bash
openclaw gateway restart
```

---

## Using in Cron Jobs

In your cron job definition, set the model to `router/router`:

```json
{
  "id": "my-cron-job",
  "schedule": "0 */2 * * *",
  "payload": {
    "kind": "agentTurn",
    "message": "Check notifications and report",
    "model": "router/router",
    "thinking": "low"
  }
}
```

### Why This Matters

- **Tools-heavy jobs**: Router detects tools and uses models that support function calling
- **Simple jobs**: Uses cheaper models automatically
- **Failures**: Falls back to alternative models without crashing

---

## Recommended Configuration for Agents

Create `router_config.json`:

```json
{
  "model_mappings": {
    "tools": [
      "openrouter/moonshotai/kimi-k2.5",
      "openrouter/z-ai/glm-5",
      "openai/gpt-4o-mini"
    ],
    "code": [
      "openrouter/z-ai/glm-5",
      "openai/gpt-4o-mini"
    ],
    "reasoning": [
      "openrouter/moonshotai/kimi-k2.5",
      "openrouter/z-ai/glm-5"
    ],
    "conversation": [
      "openrouter/z-ai/glm-5",
      "openai/gpt-4o-mini"
    ]
  }
}
```

This configuration:

1. **Prioritizes capable models for tools** — kimi-k2.5 and glm-5 handle function calling well
2. **Uses cheaper models for chat** — glm-5 is $0.05/1M input
3. **Provides fallbacks** — If OpenRouter fails, OpenAI picks up

---

## Circuit Breaker for Agents

When models fail repeatedly, router disables them automatically:

```
Model fails 3 times → Circuit OPEN (disabled)
Wait 5 minutes → Circuit HALF-OPEN (testing)
Next success → Circuit CLOSED (normal)
```

### Why This Matters for Agents

- **No infinite retry loops** — Failed model is skipped
- **Automatic recovery** — Model is re-tested after timeout
- **Agent continues** — Uses fallback models instead of crashing

### Manual Control

```bash
# Check circuit breaker status
curl http://localhost:3456/metrics | jq .circuit_breaker

# Reset a specific model
curl -X POST http://localhost:3456/circuit-breaker/reset/openai/gpt-4o

# Reset all
curl -X POST http://localhost:3456/circuit-breaker/reset-all
```

---

## Monitoring Agent Usage

### Check Metrics

```bash
curl http://localhost:3456/metrics | jq
```

Key fields:

```json
{
  "requests": {
    "total": 150,
    "success": 148,
    "failed": 2
  },
  "total_cost_usd": 0.45,
  "category_distribution": {
    "tools": 80,
    "conversation": 50,
    "code": 20
  },
  "provider_distribution": {
    "openrouter": 120,
    "openai": 30
  }
}
```

### Interpretation

- **High failed rate** → Check circuit breaker, model availability
- **High tools usage** → Expected for agent cron jobs
- **Cost tracking** → Monitor spending across all agents

---

## Common Issues

### Agent returns 422/500 errors

**Cause:** All models in fallback chain failed

**Solution:**
1. Check `circuit_breaker_state.json`
2. Reset circuits: `POST /circuit-breaker/reset-all`
3. Verify API keys are valid

### Router not reachable

**Cause:** Router process stopped

**Solution:**
```bash
# Check if running
curl http://localhost:3456/health

# Restart if needed
cd llm-router/service
uvicorn main:app --host 0.0.0.0 --port 3456
```

### Tools not working

**Cause:** Model doesn't support function calling

**Solution:** Ensure `tools` category has capable models:
```json
{
  "tools": [
    "openrouter/moonshotai/kimi-k2.5",
    "openai/gpt-4o"
  ]
}
```

---

## Best Practices

1. **Always have fallbacks** — At least 2-3 models per category
2. **Mix providers** — If one provider goes down, others continue
3. **Monitor costs** — Check `/metrics` regularly
4. **Test tool support** — Verify models in `tools` category handle function calling
5. **Keep router running** — Use systemd/cron for auto-start

---

## Auto-Start Router

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
ExecStart=/usr/bin/uvicorn main:app --host 0.0.0.0 --port 3456
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable llm-router
sudo systemctl start llm-router
```

### Windows (Task Scheduler)

1. Open "Task Scheduler"
2. Create Task → "LLM Router"
3. Trigger: "At startup"
4. Action: Start program
   - Program: `python`
   - Arguments: `-m uvicorn main:app --host 0.0.0.0 --port 3456`
   - Start in: `C:\path\to\llm-router\service`

---

## Example: Full Agent Setup

### Config

```json
{
  "model_mappings": {
    "tools": [
      "openrouter/moonshotai/kimi-k2.5",
      "openrouter/z-ai/glm-5",
      "openai/gpt-4o-mini"
    ],
    "code": [
      "openrouter/z-ai/glm-5",
      "openai/gpt-4o-mini"
    ],
    "reasoning": [
      "openrouter/moonshotai/kimi-k2.5",
      "openrouter/z-ai/glm-5"
    ],
    "conversation": [
      "openrouter/z-ai/glm-5",
      "ollama/llama3.1"
    ]
  }
}
```

### Cron Jobs

```json
[
  {
    "id": "check-github",
    "schedule": "0 * * * *",
    "payload": {
      "kind": "agentTurn",
      "message": "Check GitHub notifications",
      "model": "router/router",
      "thinking": "low"
    }
  },
  {
    "id": "daily-summary",
    "schedule": "0 8 * * *",
    "payload": {
      "kind": "agentTurn",
      "message": "Summarize yesterday's activity",
      "model": "router/router"
    }
  }
]
```

Result:
- GitHub checks (tools) → kimi-k2.5
- Summaries (reasoning) → kimi-k2.5 or glm-5
- If OpenRouter down → OpenAI picks up
- If all paid down → Ollama for conversation
