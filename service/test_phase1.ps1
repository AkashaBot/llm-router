# LLM Router Service - Phase 1 Validation Script (Windows)
# Run this to validate Phase 1 implementation

Write-Host "=== LLM Router Service - Phase 1 Validation ===" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env file not found. Copy .env.example to .env and add your API key." -ForegroundColor Red
    exit 1
}

# Check if OPENROUTER_API_KEY is set
$envContent = Get-Content ".env" -Raw
if ($envContent -notmatch "OPENROUTER_API_KEY=.*[a-zA-Z0-9]") {
    Write-Host "❌ OPENROUTER_API_KEY not set in .env" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Configuration found" -ForegroundColor Green
Write-Host ""

# Start the server in background
Write-Host "Starting server on port 3456..."
$job = Start-Job -ScriptBlock {
    param($port)
    Set-Location $PSScriptRoot
    uvicorn main:app --host 0.0.0.0 --port $port
} -ArgumentList 3456

# Wait for server to start
Write-Host "Waiting for server to start..."
Start-Sleep -Seconds 4

# Test 1: Health check
Write-Host ""
Write-Host "=== Test 1: Health Check ===" -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:3456/health" -Method Get -TimeoutSec 5
    if ($healthResponse.status -eq "healthy") {
        Write-Host "✅ Health check passed" -ForegroundColor Green
        Write-Host "   Response: $($healthResponse | ConvertTo-Json)"
    } else {
        Write-Host "❌ Health check failed" -ForegroundColor Red
        Stop-Job $job
        Remove-Job $job
        exit 1
    }
} catch {
    Write-Host "❌ Health check failed: $_" -ForegroundColor Red
    Stop-Job $job
    Remove-Job $job
    exit 1
}

# Test 2: Models endpoint
Write-Host ""
Write-Host "=== Test 2: Models Endpoint ===" -ForegroundColor Yellow
try {
    $modelsResponse = Invoke-RestMethod -Uri "http://localhost:3456/models" -Method Get -TimeoutSec 5
    if ($modelsResponse.data.id -contains "router") {
        Write-Host "✅ Models endpoint passed" -ForegroundColor Green
        Write-Host "   Response: $($modelsResponse | ConvertTo-Json -Compress)"
    } else {
        Write-Host "❌ Models endpoint failed" -ForegroundColor Red
        Stop-Job $job
        Remove-Job $job
        exit 1
    }
} catch {
    Write-Host "❌ Models endpoint failed: $_" -ForegroundColor Red
    Stop-Job $job
    Remove-Job $job
    exit 1
}

# Test 3: Chat completions
Write-Host ""
Write-Host "=== Test 3: Chat Completions ===" -ForegroundColor Yellow
$body = @{
    model = "router"
    messages = @(
        @{role = "user"; content = "Say hello in one word"}
    )
    max_tokens = 10
} | ConvertTo-Json

try {
    $chatResponse = Invoke-RestMethod -Uri "http://localhost:3456/v1/chat/completions" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 30
    if ($chatResponse.choices) {
        Write-Host "✅ Chat completions passed" -ForegroundColor Green
        $content = $chatResponse.choices[0].message.content
        Write-Host "   Response: $content"
    } else {
        Write-Host "❌ Chat completions failed - no choices in response" -ForegroundColor Red
        Stop-Job $job
        Remove-Job $job
        exit 1
    }
} catch {
    Write-Host "❌ Chat completions failed: $_" -ForegroundColor Red
    Write-Host "   This might be OK if API key is invalid" -ForegroundColor Yellow
    Stop-Job $job
    Remove-Job $job
    exit 1
}

# Cleanup
Stop-Job $job
Remove-Job $job

Write-Host ""
Write-Host "=== All Phase 1 Tests Passed! ✅ ===" -ForegroundColor Green
Write-Host ""
Write-Host "To run the service permanently:" -ForegroundColor Cyan
Write-Host "  uvicorn main:app --host 0.0.0.0 --port 3456" -ForegroundColor White
Write-Host ""
Write-Host "To configure OpenClaw, see integration.md" -ForegroundColor Cyan