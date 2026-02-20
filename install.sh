#!/bin/bash
# LLM Router Installer
# Usage: ./install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROUTER_DIR="$(dirname "$SCRIPT_DIR")"
OPENCLAW_DIR="${OPENCLAW_DIR:-$HOME/.openclaw}"

echo "🔮 Installing LLM Router..."

# 1. Install Python dependencies
echo "📦 Installing Python dependencies..."
cd "$ROUTER_DIR/service"
pip install -r requirements.txt

# 2. Copy .env.example to .env if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit $ROUTER_DIR/service/.env with your API keys"
fi

# 3. Install OpenClaw skill
echo "🔧 Installing OpenClaw skill..."
mkdir -p "$OPENCLAW_DIR/skills/llm-router"
cp "$ROUTER_DIR/skill/"* "$OPENCLAW_DIR/skills/llm-router/" 2>/dev/null || cp "$ROUTER_DIR/../skills/llm-router/"* "$OPENCLAW_DIR/skills/llm-router/" 2>/dev/null || true

# 4. Add cron job for health check
echo "⏰ Adding health-check cron job..."
CRON_JOB="*/5 * * * * $ROUTER_DIR/scripts/health-check.sh"

# Check if cron job already exists
if ! crontab -l 2>/dev/null | grep -q "llm-router.*health-check"; then
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Cron job added (every 5 minutes)"
else
    echo "ℹ️  Cron job already exists"
fi

# 5. Add to crontab @reboot for auto-start
BOOT_JOB="@reboot $ROUTER_DIR/scripts/start.sh"
if ! crontab -l 2>/dev/null | grep -q "llm-router.*start.sh"; then
    (crontab -l 2>/dev/null; echo "$BOOT_JOB") | crontab -
    echo "✅ Boot auto-start added"
fi

# 6. Make scripts executable
chmod +x "$ROUTER_DIR/scripts/"*.sh 2>/dev/null || true

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit $ROUTER_DIR/service/.env with your API keys"
echo "2. Run: $ROUTER_DIR/scripts/start.sh"
echo "3. Or restart OpenClaw gateway"
echo ""
echo "Commands available:"
echo "  /router status  - Check router health"
echo "  /router config  - View configuration"
echo "  /router costs   - See accumulated costs"
