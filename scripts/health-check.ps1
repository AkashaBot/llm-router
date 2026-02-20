# PowerShell Health Check for Windows
# Run via Task Scheduler every 5 minutes

param(
    [string]$RouterUrl = "http://localhost:3456",
    [string]$RouterDir = "$PSScriptRoot\..\service"
)

$LogFile = Join-Path $RouterDir "health.log"

function Write-Log {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$Timestamp] $Message" | Out-File -FilePath $LogFile -Append
}

function Test-Router {
    try {
        $response = Invoke-RestMethod -Uri "$RouterUrl/health" -Method Get -TimeoutSec 5
        return $response.status -eq "healthy"
    } catch {
        return $false
    }
}

function Test-ModelsAvailable {
    try {
        $metrics = Invoke-RestMethod -Uri "$RouterUrl/metrics" -Method Get -TimeoutSec 5
        # If all circuits are open, models are unavailable
        $openCircuits = $metrics.circuit_breaker.open_circuits
        return ($openCircuits.PSObject.Properties.Count -eq 0)
    } catch {
        return $false
    }
}

function Reset-Circuits {
    try {
        Invoke-RestMethod -Uri "$RouterUrl/circuit-breaker/reset-all" -Method Post -TimeoutSec 5 | Out-Null
        Write-Log "Circuit breakers reset"
    } catch {
        Write-Log "Failed to reset circuits: $_"
    }
}

function Start-Router {
    Write-Log "Router down, starting..."
    
    Push-Location $RouterDir
    
    # Start in background
    $process = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3456" -PassThru -WindowStyle Hidden
    
    Start-Sleep -Seconds 3
    
    if (Test-Router) {
        Write-Log "Router restarted successfully (PID: $($process.Id))"
    } else {
        Write-Log "Failed to restart router"
    }
    
    Pop-Location
}

# Main
if (-not (Test-Router)) {
    Start-Router
} elseif (-not (Test-ModelsAvailable)) {
    Write-Log "All models circuit-open, resetting circuits..."
    Reset-Circuits
}
