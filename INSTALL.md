# Quick Install

## Linux / macOS

```bash
cd llm-router
chmod +x install.sh
./install.sh
```

## Windows

```powershell
cd llm-router
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Bypass -Force
.\install.ps1
```

## What it does

1. ✅ Install Python dependencies
2. ✅ Create `.env` from template
3. ✅ Install OpenClaw skill (`~/.openclaw/skills/llm-router`)
4. ✅ Add health-check cron (every 5 min)
5. ✅ Add boot auto-start

## After install

1. Edit `.env` with your API keys
2. Restart OpenClaw: `openclaw gateway restart`
3. Test: `/router status`

## Manual start

```bash
# Linux/macOS
./scripts/start.sh

# Windows
scripts\start.bat
```
