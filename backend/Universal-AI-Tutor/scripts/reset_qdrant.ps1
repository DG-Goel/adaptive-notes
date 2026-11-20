# Reset Qdrant by removing all data and restarting
# WARNING: This will delete all indexed documents and collections!
# Usage: .\scripts\reset_qdrant.ps1

Write-Host "WARNING: This will delete all Qdrant data!" -ForegroundColor Red
$confirmation = Read-Host "Are you sure you want to continue? (yes/no)"

if ($confirmation -ne "yes") {
    Write-Host "Aborted." -ForegroundColor Yellow
    exit 0
}

Write-Host "`nStopping Qdrant..." -ForegroundColor Yellow
docker compose down

Write-Host "Removing Qdrant data..." -ForegroundColor Yellow
$dataDir = Join-Path $PSScriptRoot "..\data\qdrant_storage"
if (Test-Path $dataDir) {
    Remove-Item -Path $dataDir -Recurse -Force
    Write-Host "✓ Data directory removed" -ForegroundColor Green
}

Write-Host "Recreating data directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $dataDir -Force | Out-Null

Write-Host "Starting fresh Qdrant instance..." -ForegroundColor Yellow
docker compose up -d

if ($LASTEXITCODE -eq 0) {
    Start-Sleep -Seconds 3
    Write-Host "`n✓ Qdrant has been reset successfully!" -ForegroundColor Green
    Write-Host "  Dashboard: http://localhost:6333/dashboard" -ForegroundColor Cyan
} else {
    Write-Host "ERROR: Failed to restart Qdrant" -ForegroundColor Red
    exit 1
}
