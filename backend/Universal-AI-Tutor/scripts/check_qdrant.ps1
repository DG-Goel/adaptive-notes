# Check Qdrant health and connection
# Usage: .\scripts\check_qdrant.ps1

Write-Host "Checking Qdrant status..." -ForegroundColor Cyan

# Check if container is running
$container = docker ps --filter "name=universal-ai-tutor-qdrant" --format "{{.Names}}"

if (-not $container) {
    Write-Host "✗ Qdrant container is not running" -ForegroundColor Red
    Write-Host "  Start it with: docker compose up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Qdrant container is running" -ForegroundColor Green

# Check health endpoint
Write-Host "`nChecking REST API health..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "http://localhost:6333/health" -Method Get -ErrorAction Stop
    Write-Host "✓ REST API is healthy" -ForegroundColor Green
    Write-Host "  Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Gray
} catch {
    Write-Host "✗ REST API health check failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Get collections
Write-Host "`nChecking collections..." -ForegroundColor Cyan
try {
    $collections = Invoke-RestMethod -Uri "http://localhost:6333/collections" -Method Get -ErrorAction Stop
    $collectionCount = $collections.result.collections.Count
    
    if ($collectionCount -eq 0) {
        Write-Host "  No collections found (expected for fresh install)" -ForegroundColor Yellow
    } else {
        Write-Host "✓ Found $collectionCount collection(s):" -ForegroundColor Green
        foreach ($col in $collections.result.collections) {
            Write-Host "  - $($col.name)" -ForegroundColor Cyan
        }
    }
} catch {
    Write-Host "✗ Failed to retrieve collections: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`n✓ Qdrant is fully operational!" -ForegroundColor Green
Write-Host "  Dashboard: http://localhost:6333/dashboard" -ForegroundColor Cyan
