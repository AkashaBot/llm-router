# LLM Router Skill

Provides commands to monitor and manage the LLM Router service from within OpenClaw.

## Commands

| Command | Description |
|---------|-------------|
| `/router status` | Health check and quick metrics |
| `/router config` | Show current routing configuration |
| `/router reload` | Reload configuration from file |
| `/router reset` | Reset all circuit breakers |
| `/router models` | List models by category |
| `/router costs` | Show accumulated costs |

## Usage

Just type any of the commands above in a chat with the agent.

## Requirements

- LLM Router running on `http://localhost:3456` (configurable via ROUTER_URL env var)
- Agent must have network access to the router

## Example

```
User: /router status
Agent: 🟢 Router healthy
       - Requests: 45 (98% success)
       - Cost: $0.12 today
       - Models: kimi-k2.5, glm-5, qwen3-1.7b
```
