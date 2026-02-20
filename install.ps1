# LLM Router Installer for Windows
# Run in PowerShell: .\install.ps1

param(
    [string]$OpenClawDir = "$env:USERPROFILE\.openclaw",
    [string]$RouterDir = $PSScriptRoot
)

$ErrorActionPreference = "Stop"

Write-Host "🔮 Installing LLM Router..." -ForegroundColor Cyan

# 1. Install Python dependencies
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
Push-Location "$RouterDir\service"
pip install -r requirements.txt
Pop-Location

# 2. Copy .env.example to .env if not exists
if (-not (Test-Path "$RouterDir\service\.env")) {
    Write-Host "📝 Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item "$RouterDir\service\.env.example" "$RouterDir\service\.env"
    Write-Host "⚠️  Please edit $RouterDir\service\.env with your API keys" -ForegroundColor Yellow
}

# 3. Install OpenClaw skill
Write-Host "🔧 Installing OpenClaw skill..." -ForegroundColor Yellow
$SkillDir = "$OpenClawDir\skills\llm-router"
New-Item -ItemType Directory -Force -Path $SkillDir | Out-Null

# Copy from skill folder or skills folder
if (Test-Path "$RouterDir\skill\SKILL.md") {
    Copy-Item "$RouterDir\skill\*" $SkillDir -Force
} elseif (Test-Path "$RouterDir\..\skills\llm-router\SKILL.md") {
    Copy-Item "$RouterDir\..\skills\llm-router\*" $SkillDir -Force
}

Write-Host "✅ Skill installed to $SkillDir" -ForegroundColor Green

# 4. Add cron job for health check
Write-Host "⏰ Adding health-check cron job..." -ForegroundColor Yellow

$CronJobsPath = "$OpenClawDir\cron\jobs.json"

# Read existing jobs or create new
if (Test-Path $CronJobsPath) {
    $jobs = Get-Content $CronJobsPath | ConvertFrom-Json
} else {
    $jobs = @{ jobs = @() }
}

# Check if job already exists (every 1 minute for stability)
$existingJob = $jobs.jobs | Where-Object { $_.id -eq "llm-router-health-check" }

if (-not $existingJob) {
    $newJob = @{
        id = "llm-router-health-check"
        enabled = $true
        schedule = "*/1 * * * *"  # Every 1 minute for quick recovery
        timezone = "Europe/Paris"
        payload = @{
            kind = "shell"
            command = "powershell"
            args = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "$RouterDir\scripts\health-check.ps1")
        }
    }
    
    $jobs.jobs += $newJob
    $jobs | ConvertTo-Json -Depth 10 | Out-File $CronJobsPath -Encoding UTF8
    Write-Host "✅ Cron job added (every 5 minutes)" -ForegroundColor Green
} else {
    Write-Host "ℹ️  Cron job already exists" -ForegroundColor Cyan
}

# 5. Instructions for auto-start
Write-Host ""
Write-Host "📋 For auto-start at boot, add a Windows Task Scheduler task:" -ForegroundColor Yellow
Write-Host "   1. Open Task Scheduler (taskschd.msc)" -ForegroundColor White
Write-Host "   2. Create Task → 'LLM Router'" -ForegroundColor White
Write-Host "   3. Trigger: 'At startup'" -ForegroundColor White
Write-Host "   4. Action: Start program" -ForegroundColor White
Write-Host "      Program: powershell" -ForegroundColor White
Write-Host "      Arguments: -ExecutionPolicy Bypass -File $RouterDir\scripts\start.bat" -ForegroundColor White

Write-Host ""
Write-Host "✅ Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit $RouterDir\service\.env with your API keys" -ForegroundColor White
Write-Host "2. Restart OpenClaw gateway: openclaw gateway restart" -ForegroundColor White
Write-Host "3. Or start manually: $RouterDir\scripts\start.bat" -ForegroundColor White
Write-Host ""
Write-Host "Commands available:" -ForegroundColor Cyan
Write-Host "  /router status  - Check router health" -ForegroundColor White
Write-Host "  /router config  - View configuration" -ForegroundColor White
Write-Host "  /router costs   - See accumulated costs" -ForegroundColor White
