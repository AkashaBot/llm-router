# LLM Router Skill for OpenClaw

Provides commands to monitor and manage the LLM Router service.

## Installation

Copy this folder to your OpenClaw skills directory:
```
~/.openclaw/skills/llm-router/
```

Or clone directly:
```bash
git clone https://github.com/AkashaBot/llm-router.git
cp -r llm-router/skill ~/.openclaw/skills/llm-router
```

## Commands

| Command | Description |
|---------|-------------|
| `/router status` | Health check and quick metrics |
| `/router config` | Show current routing configuration |
| `/router reload` | Reload configuration from file |
| `/router reset` | Reset all circuit breakers |
| `/router models` | List models by category with costs |
| `/router costs` | Show accumulated costs |

## Example

```
User: /router status
Agent: 🟢 Router healthy (v0.5.0)

       📊 Requests: 45 (98% success)
       💰 Cost: $0.12
       ⏱️ Avg latency: 1234ms
       
       Providers: openrouter, openai
       Categories: tools, code, reasoning
```

## Configuration

Set the router URL via environment variable:
```bash
export ROUTER_URL=http://localhost:3456
```

Default: `http://localhost:3456`

## Requirements

- LLM Router v0.5.0+
- Python 3.8+
- httpx library
