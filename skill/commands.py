# LLM Router Commands

import os
import httpx

ROUTER_URL = os.getenv("ROUTER_URL", "http://localhost:3456")

async def router_status():
    """Get router health and quick metrics"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            health = await client.get(f"{ROUTER_URL}/health")
            metrics = await client.get(f"{ROUTER_URL}/metrics")
            
            h = health.json()
            m = metrics.json()
            
            success_rate = (m["requests"]["success"] / m["requests"]["total"] * 100) if m["requests"]["total"] > 0 else 0
            
            return f"""🟢 **Router {h['status']}** (v{h['version']})

📊 **Requests:** {m['requests']['total']} ({success_rate:.0f}% success)
💰 **Cost:** ${m['total_cost_usd']:.4f}
⏱️ **Avg latency:** {m['avg_latency_ms']:.0f}ms

**Providers:** {', '.join(m.get('provider_distribution', {}).keys()) or 'N/A'}
**Categories:** {', '.join(m.get('category_distribution', {}).keys()) or 'N/A'}"""
        except Exception as e:
            return f"🔴 Router unreachable: {e}"

async def router_config():
    """Show current routing configuration"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"{ROUTER_URL}/config")
            c = resp.json()
            
            lines = ["📋 **Router Configuration**\n"]
            lines.append(f"**Routing mode:** {c['routing_mode']}\n")
            lines.append("**Model mappings:**")
            for cat, models in c.get('model_mappings', {}).items():
                lines.append(f"- **{cat}:** {' → '.join(models[:2])}")
            
            return "\n".join(lines)
        except Exception as e:
            return f"🔴 Error: {e}"

async def router_reload():
    """Reload configuration from file"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.post(f"{ROUTER_URL}/config/reload")
            r = resp.json()
            return f"✅ Config reloaded\nCategories: {', '.join(r.get('categories', []))}"
        except Exception as e:
            return f"🔴 Error: {e}"

async def router_reset():
    """Reset all circuit breakers"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            await client.post(f"{ROUTER_URL}/circuit-breaker/reset-all")
            return "✅ All circuit breakers reset"
        except Exception as e:
            return f"🔴 Error: {e}"

async def router_models():
    """List models by category"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"{ROUTER_URL}/config")
            c = resp.json()
            
            lines = ["📊 **Models by Category**\n"]
            for cat, models in c.get('model_mappings', {}).items():
                lines.append(f"**{cat}:**")
                for i, m in enumerate(models, 1):
                    cost = c.get('model_costs', {}).get(m, {})
                    cost_str = f"(${cost.get('input', '?')}/{cost.get('output', '?')})" if cost else ""
                    marker = "→ " if i == 1 else "  "
                    lines.append(f"  {marker}{m} {cost_str}")
            
            return "\n".join(lines)
        except Exception as e:
            return f"🔴 Error: {e}"

async def router_costs():
    """Show accumulated costs"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"{ROUTER_URL}/metrics")
            m = resp.json()
            
            lines = ["💰 **Router Costs**\n"]
            lines.append(f"**Total:** ${m['total_cost_usd']:.4f}")
            lines.append(f"**Requests:** {m['requests']['total']}")
            lines.append(f"**Avg per request:** ${m['total_cost_usd']/m['requests']['total']:.6f}" if m['requests']['total'] > 0 else "")
            lines.append("\n**By model:**")
            for model, count in sorted(m.get('model_distribution', {}).items(), key=lambda x: -x[1]):
                lines.append(f"- {model}: {count} requests")
            
            return "\n".join(lines)
        except Exception as e:
            return f"🔴 Error: {e}"

# Command registry
COMMANDS = {
    "/router status": router_status,
    "/router config": router_config,
    "/router reload": router_reload,
    "/router reset": router_reset,
    "/router models": router_models,
    "/router costs": router_costs,
}
