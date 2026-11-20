# Start Qdrant using Docker Compose
# Usage: .\scripts\start_qdrant.ps1

Write-Host "Starting Qdrant v1.20.1..." -ForegroundColor Green

# Check if Docker is running
$dockerRunning = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Create data directory if it doesn't exist
$dataDir = Join-Path $PSScriptRoot "..\data\qdrant_storage"
if (-not (Test-Path $dataDir)) {
    Write-Host "Creating Qdrant storage directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
}

# Start Qdrant
Write-Host "Launching Qdrant container..." -ForegroundColor Yellow
docker compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nQdrant started successfully!" -ForegroundColor Green
    Write-Host "REST API: http://localhost:6333" -ForegroundColor Cyan
    Write-Host "gRPC API: localhost:6334" -ForegroundColor Cyan
    Write-Host "Dashboard: http://localhost:6333/dashboard" -ForegroundColor Cyan
    Write-Host "`nChecking health status..." -ForegroundColor Yellow
    
    # Wait a moment for container to be ready
    Start-Sleep -Seconds 3
    
    # Test connection
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:6333/health" -UseBasicParsing -ErrorAction Stop
        Write-Host "✓ Qdrant is healthy and ready!" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Qdrant container started but health check failed. It may still be initializing..." -ForegroundColor Yellow
        Write-Host "  Wait 10-20 seconds and try: curl http://localhost:6333/health" -ForegroundColor Yellow
    }
} else {
    Write-Host "`nERROR: Failed to start Qdrant" -ForegroundColor Red
    exit 1
}

Write-Host "`nTo stop Qdrant: docker compose down" -ForegroundColor Gray
Write-Host "To view logs: docker compose logs -f qdrant" -ForegroundColor Gray
