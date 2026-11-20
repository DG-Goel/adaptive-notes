# Phase 1 Acceptance Test Execution Script
# Runs all test suites and reports comprehensive results

Write-Host "`n=== Universal AI Tutor - Phase 1 Acceptance Tests ===`n" -ForegroundColor Cyan

$TestResults = @{
    UnitTests = @{Passed=0; Failed=0; Skipped=0; Total=0; Duration=0}
    IntegrationTests = @{Passed=0; Failed=0; Skipped=0; Total=0; Duration=0}
    OverallPassed = 0
    OverallFailed = 0
    OverallSkipped = 0
    OverallTotal = 0
    OverallDuration = 0
}

# Run Unit Tests
Write-Host "Running Unit Tests..." -ForegroundColor Yellow
$UnitOutput = py -3.12 -m pytest tests/unit/ -v --tb=short -q 2>&1 | Out-String
$UnitOutput | Out-File "unit_test_results.txt"

if ($UnitOutput -match "(\d+) passed") {
    $TestResults.UnitTests.Passed = [int]$matches[1]
}
if ($UnitOutput -match "(\d+) failed") {
    $TestResults.UnitTests.Failed = [int]$matches[1]
}
if ($UnitOutput -match "(\d+) skipped") {
    $TestResults.UnitTests.Skipped = [int]$matches[1]
}
if ($UnitOutput -match "in ([\d\.]+)s") {
    $TestResults.UnitTests.Duration = [decimal]$matches[1]
}
$TestResults.UnitTests.Total = $TestResults.UnitTests.Passed + $TestResults.UnitTests.Failed + $TestResults.UnitTests.Skipped

Write-Host "Unit Tests: $($TestResults.UnitTests.Passed) passed, $($TestResults.UnitTests.Failed) failed, $($TestResults.UnitTests.Skipped) skipped" -ForegroundColor Green

# Run Integration Tests (with longer timeout tolerance)
Write-Host "`nRunning Integration Tests (this may take several minutes)..." -ForegroundColor Yellow

# Run integration tests in smaller groups to avoid timeout
$IntegrationModules = @(
    "test_api.py",
    "test_context_expansion.py",
    "test_document_updates.py",
    "test_ingestion_service.py",
    "test_source_fidelity.py",
    "test_vector_store.py"
)

$IntegrationPassed = 0
$IntegrationFailed = 0
$IntegrationSkipped = 0
$IntegrationDuration = 0

foreach ($module in $IntegrationModules) {
    Write-Host "  Running $module..." -ForegroundColor Gray
    $output = py -3.12 -m pytest "tests/integration/$module" -v --tb=short -q 2>&1 | Out-String
    $output | Out-File "integration_${module}_results.txt"
    
    if ($output -match "(\d+) passed") {
        $IntegrationPassed += [int]$matches[1]
    }
    if ($output -match "(\d+) failed") {
        $IntegrationFailed += [int]$matches[1]
    }
    if ($output -match "(\d+) skipped") {
        $IntegrationSkipped += [int]$matches[1]
    }
    if ($output -match "in ([\d\.]+)s") {
        $IntegrationDuration += [decimal]$matches[1]
    }
}

$TestResults.IntegrationTests.Passed = $IntegrationPassed
$TestResults.IntegrationTests.Failed = $IntegrationFailed
$TestResults.IntegrationTests.Skipped = $IntegrationSkipped
$TestResults.IntegrationTests.Duration = $IntegrationDuration
$TestResults.IntegrationTests.Total = $IntegrationPassed + $IntegrationFailed + $IntegrationSkipped

Write-Host "Integration Tests: $IntegrationPassed passed, $IntegrationFailed failed, $IntegrationSkipped skipped" -ForegroundColor Green

# Calculate Overall Results
$TestResults.OverallPassed = $TestResults.UnitTests.Passed + $TestResults.IntegrationTests.Passed
$TestResults.OverallFailed = $TestResults.UnitTests.Failed + $TestResults.IntegrationTests.Failed
$TestResults.OverallSkipped = $TestResults.UnitTests.Skipped + $TestResults.IntegrationTests.Skipped
$TestResults.OverallTotal = $TestResults.OverallPassed + $TestResults.OverallFailed + $TestResults.OverallSkipped
$TestResults.OverallDuration = $TestResults.UnitTests.Duration + $TestResults.IntegrationTests.Duration

# Print Summary
Write-Host "`n=== TEST EXECUTION SUMMARY ===" -ForegroundColor Cyan
Write-Host "Unit Tests:        $($TestResults.UnitTests.Passed)/$($TestResults.UnitTests.Total) passed ($($TestResults.UnitTests.Duration)s)" -ForegroundColor White
Write-Host "Integration Tests: $($TestResults.IntegrationTests.Passed)/$($TestResults.IntegrationTests.Total) passed ($($TestResults.IntegrationTests.Duration)s)" -ForegroundColor White
Write-Host "`nOVERALL:           $($TestResults.OverallPassed)/$($TestResults.OverallTotal) passed ($($TestResults.OverallDuration)s)" -ForegroundColor $(if ($TestResults.OverallFailed -eq 0) { "Green" } else { "Red" })

if ($TestResults.OverallFailed -gt 0) {
    Write-Host "`n⚠️  WARNING: $($TestResults.OverallFailed) test(s) failed!" -ForegroundColor Red
    Write-Host "Review test output files for details." -ForegroundColor Yellow
}

# Export results to JSON
$TestResults | ConvertTo-Json -Depth 3 | Out-File "test_results_summary.json"

Write-Host "`nTest results exported to test_results_summary.json" -ForegroundColor Cyan
