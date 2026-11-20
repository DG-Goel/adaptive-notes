# Stop Qdrant Docker container
# Usage: .\scripts\stop_qdrant.ps1

Write-Host "Stopping Qdrant..." -ForegroundColor Yellow

docker compose down

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Qdrant stopped successfully" -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to stop Qdrant" -ForegroundColor Red
    exit 1
}
