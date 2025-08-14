# Mock Vista API server and Podman API management for Windows
param([string]$Action = "help")

function Start-MockServer {
    Write-Host "Starting mock server..." -ForegroundColor Green
    
    # First expose Podman API for devcontainer access
    Write-Host "Exposing Podman API on port 2375..." -ForegroundColor Yellow
    $apiJob = Get-Job -Name "PodmanAPI" -ErrorAction SilentlyContinue
    if (-not $apiJob -or $apiJob.State -ne "Running") {
        $job = Start-Job -Name "PodmanAPI" -ScriptBlock {
            podman machine ssh -- sudo podman system service --time=0 tcp://0.0.0.0:2375
        }
        Start-Sleep -Seconds 3
    }
    
    # Start mock server containers
    Push-Location "$PSScriptRoot\..\mock_server"
    docker-compose up -d
    Pop-Location
    
    Write-Host "✅ Mock server running at http://localhost:8888" -ForegroundColor Green
    Write-Host "✅ Podman API exposed on port 2375 for devcontainer" -ForegroundColor Green
}

function Stop-MockServer {
    Write-Host "Stopping services..." -ForegroundColor Yellow
    
    # Stop mock server
    Push-Location "$PSScriptRoot\..\mock_server"
    docker-compose down
    Pop-Location
    
    # Stop Podman API
    Get-Job -Name "PodmanAPI" -ErrorAction SilentlyContinue | Stop-Job | Remove-Job
    
    Write-Host "✅ Stopped" -ForegroundColor Green
}

function Show-Status {
    Write-Host "Checking services..." -ForegroundColor Cyan
    
    # Check containers
    podman ps --format "table {{.Names}}\t{{.Status}}"
    
    # Check Podman API
    Write-Host "`nPodman API Status:" -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:2375/_ping" -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ API is responding on port 2375" -ForegroundColor Green
        }
    } catch {
        Write-Host "❌ API is not responding on port 2375" -ForegroundColor Red
    }
}

switch ($Action.ToLower()) {
    "start" { Start-MockServer }
    "stop" { Stop-MockServer }
    "status" { Show-Status }
    default {
        Write-Host "Usage: .\mock-server.ps1 [start|stop|status]" -ForegroundColor Yellow
        Write-Host "  start  - Start mock server and expose Podman API"
        Write-Host "  stop   - Stop mock server and Podman API"
        Write-Host "  status - Show running containers and API status"
    }
}