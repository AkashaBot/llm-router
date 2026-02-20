# LLM Router

**Intelligent model routing for LLM applications.**

Automatically selects the best model for each request based on task type, with multi-provider support, cost tracking, and automatic failover.

---

## The Problem

LLM applications face a common challenge:

- **Different tasks need different models** — code generation, reasoning, conversation, function calling
- **Providers have different strengths** — OpenAI excels at tools, Anthropic at reasoning, local models for privacy
- **Costs vary wildly** — from $0.05 to $15 per million tokens
- **Failures happen** — rate limits, outages, API errors

## The Solution

LLM Router acts as an intelligent proxy:

```
Your App → LLM Router → Best Model for Task
                    ↓
            OpenRouter / OpenAI / Anthropic / Google / Ollama
```

**How it works:**

1. **Detect** — Analyzes the request to determine task type (code, reasoning, conversation, tools)
2. **Route** — Selects the optimal model from your configured providers
3. **Fallback** — If the primary model fails, automatically tries alternatives
4. **Track** — Records latency, cost, and success rates

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-provider** | OpenRouter, OpenAI, Anthropic, Google AI, Ollama |
| **Smart routing** | Keyword-based or LLM-based classification |
| **Circuit breaker** | Auto-disable failing models, auto-retry after recovery |
| **Cost tracking** | Real-time USD cost estimation per request |
| **Custom categories** | Define your own task types and model chains |
| **OpenAI-compatible** | Drop-in replacement for OpenAI API |

---

## Quick Start

```bash
# Install
pip install fastapi httpx python-dotenv

# Configure
export OPENROUTER_API_KEY=sk-or-v1-...

# Run
uvicorn main:app --host 0.0.0.0 --port 3456

# Use
curl http://localhost:3456/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"router","messages":[{"role":"user","content":"Hello"}]}'
```

---

## Routing Logic

### Categories

| Category | Detection | Example Models |
|----------|-----------|----------------|
| **tools** | Request contains `tools` array | kimi-k2.5, gpt-4o |
| **code** | Keywords: python, function, debug... | glm-5, gpt-4o-mini |
| **reasoning** | Keywords: why, how, explain... | kimi-k2.5, claude-3 |
| **conversation** | Short messages, greetings | glm-5, gpt-4o-mini |

### Fallback Chain

Each category has a fallback chain:

```
tools: kimi-k2.5 → glm-5 → gpt-4o-mini
       ↓ fail     ↓ fail   ↓ success
```

If `kimi-k2.5` fails, router tries `glm-5`, then `gpt-4o-mini`.

---

## Multi-Provider

Mix providers in the same fallback chain:

```json
{
  "tools": [
    "openrouter/moonshotai/kimi-k2.5",
    "openai/gpt-4o",
    "anthropic/claude-3-sonnet"
  ],
  "conversation": [
    "openrouter/z-ai/glm-5",
    "ollama/llama3.1"
  ]
}
```

If all paid providers fail, fall back to local Ollama (free).

---

## For OpenClaw Agents

### Configuration

Add to `~/.openclaw/openclaw.json`:

```json
{
  "models": {
    "providers": {
      "router": {
        "baseUrl": "http://localhost:3456",
        "api": "openai-completions",
        "models": [{"id": "router", "name": "LLM Router"}]
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

### Using in Cron Jobs

```json
{
  "payload": {
    "kind": "agentTurn",
    "message": "Your task here...",
    "model": "router/router"
  }
}
```

### Why OpenClaw Agents Should Use Router

| Benefit | Description |
|---------|-------------|
| **Automatic optimization** | Tools-heavy cron jobs → models that support function calling |
| **Resilience** | If primary model fails, automatically tries alternatives |
| **Cost awareness** | Track spending across all agent operations |
| **No code changes** | Drop-in replacement, just change the model ID |

### Recommended Setup for Agents

```json
{
  "model_mappings": {
    "tools": [
      "openrouter/moonshotai/kimi-k2.5",
      "openai/gpt-4o",
      "anthropic/claude-3-sonnet"
    ],
    "conversation": [
      "openrouter/z-ai/glm-5",
      "openai/gpt-4o-mini"
    ]
  }
}
```

This ensures:
- Cron jobs with tools use capable models
- Simple checks use cheaper models
- Failures don't crash your agents

---

## API Reference

### Chat Completions

```bash
POST /v1/chat/completions
POST /chat/completions  # OpenClaw alias
```

OpenAI-compatible request/response.

### Monitoring

```bash
GET /health              # Health check
GET /metrics             # Usage, cost, circuit breaker status
GET /providers           # Configured providers
```

### Configuration

```bash
GET /config
POST /config/category        # Add custom category
POST /config/model-mapping   # Update category models
DELETE /config/category/{n}  # Remove category
```

### Circuit Breaker

```bash
POST /circuit-breaker/reset/{model}  # Reset one model
POST /circuit-breaker/reset-all      # Reset all
```

---

## Installation Options

### Local

```bash
git clone https://github.com/AkashaBot/llm-router.git
cd llm-router/service
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 3456
```

### Docker

```bash
docker run -p 3456:3456 \
  -e OPENROUTER_API_KEY=sk-or-v1-... \
  ghcr.io/akashabot/llm-router:latest
```

### Systemd (Linux)

```ini
[Unit]
Description=LLM Router
After=network.target

[Service]
ExecStart=/usr/bin/uvicorn main:app --host 0.0.0.0 --port 3456
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Documentation

| Document | Content |
|----------|---------|
| [**docs/OPENCLAW-AGENTS.md**](docs/OPENCLAW-AGENTS.md) | **Guide for OpenClaw agents** |
| [service/README.md](service/README.md) | Quick usage guide |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Configuration details |
| [docs/API.md](docs/API.md) | API reference |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Deployment guides |

---

## License

MIT

---

**Repository:** https://github.com/AkashaBot/llm-router
