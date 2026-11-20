# Phase 1 Acceptance - Complete Test Execution with Accurate Reporting
# Uses pytest JUnit XML output for reliable test counting

Write-Host "`n=== Universal AI Tutor - Phase 1 Complete Test Suite ===`n" -ForegroundColor Cyan

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$resultsDir = "test_results_$timestamp"
New-Item -ItemType Directory -Path $resultsDir -Force | Out-Null

Write-Host "Test results will be saved to: $resultsDir`n" -ForegroundColor Gray

# Function to parse JUnit XML and extract test counts
function Get-TestResultsFromXML {
    param([string]$xmlPath)
    
    if (-not (Test-Path $xmlPath)) {
        return @{
            Total = 0
            Passed = 0
            Failed = 0
            Skipped = 0
            Errors = 0
            Duration = 0
        }
    }
    
    [xml]$xml = Get-Content $xmlPath
    # Handle both <testsuite> and <testsuites><testsuite> structures
    $testsuite = if ($xml.testsuites) { $xml.testsuites.testsuite } else { $xml.testsuite }
    
    $total = [int]$testsuite.tests
    $failures = [int]$testsuite.failures
    $errors = [int]$testsuite.errors
    $skipped = [int]$testsuite.skipped
    $passed = $total - $failures - $errors - $skipped
    
    return @{
        Total = $total
        Passed = $passed
        Failed = $failures
        Skipped = $skipped
        Errors = $errors
        Duration = [decimal]$testsuite.time
    }
}

# Run Unit Tests
Write-Host "Running Unit Tests..." -ForegroundColor Yellow
$unitXml = Join-Path $resultsDir "unit_tests.xml"
$unitLog = Join-Path $resultsDir "unit_tests.log"

py -3.12 -m pytest tests/unit/ -v --tb=short --junit-xml=$unitXml 2>&1 | Tee-Object -FilePath $unitLog | Out-Null
$unitExitCode = $LASTEXITCODE

$unitResults = Get-TestResultsFromXML $unitXml

Write-Host "  Collected: $($unitResults.Total)" -ForegroundColor White
Write-Host "  Passed:    $($unitResults.Passed)" -ForegroundColor Green
Write-Host "  Failed:    $($unitResults.Failed)" -ForegroundColor $(if ($unitResults.Failed -eq 0) { "Green" } else { "Red" })
Write-Host "  Skipped:   $($unitResults.Skipped)" -ForegroundColor Yellow
Write-Host "  Errors:    $($unitResults.Errors)" -ForegroundColor $(if ($unitResults.Errors -eq 0) { "Green" } else { "Red" })
Write-Host "  Duration:  $($unitResults.Duration)s`n" -ForegroundColor Gray

# Run Integration Tests
Write-Host "Running Integration Tests..." -ForegroundColor Yellow
$integrationXml = Join-Path $resultsDir "integration_tests.xml"
$integrationLog = Join-Path $resultsDir "integration_tests.log"

py -3.12 -m pytest tests/integration/ -v --tb=short --junit-xml=$integrationXml 2>&1 | Tee-Object -FilePath $integrationLog | Out-Null
$integrationExitCode = $LASTEXITCODE

$integrationResults = Get-TestResultsFromXML $integrationXml

Write-Host "  Collected: $($integrationResults.Total)" -ForegroundColor White
Write-Host "  Passed:    $($integrationResults.Passed)" -ForegroundColor Green
Write-Host "  Failed:    $($integrationResults.Failed)" -ForegroundColor $(if ($integrationResults.Failed -eq 0) { "Green" } else { "Red" })
Write-Host "  Skipped:   $($integrationResults.Skipped)" -ForegroundColor Yellow
Write-Host "  Errors:    $($integrationResults.Errors)" -ForegroundColor $(if ($integrationResults.Errors -eq 0) { "Green" } else { "Red" })
Write-Host "  Duration:  $($integrationResults.Duration)s`n" -ForegroundColor Gray

# Calculate totals
$totalCollected = $unitResults.Total + $integrationResults.Total
$totalPassed = $unitResults.Passed + $integrationResults.Passed
$totalFailed = $unitResults.Failed + $integrationResults.Failed
$totalSkipped = $unitResults.Skipped + $integrationResults.Skipped
$totalErrors = $unitResults.Errors + $integrationResults.Errors
$totalDuration = $unitResults.Duration + $integrationResults.Duration

# Print summary
Write-Host "=== OVERALL TEST RESULTS ===" -ForegroundColor Cyan
Write-Host "Total Collected: $totalCollected" -ForegroundColor White
Write-Host "Passed:          $totalPassed" -ForegroundColor Green
Write-Host "Failed:          $totalFailed" -ForegroundColor $(if ($totalFailed -eq 0) { "Green" } else { "Red" })
Write-Host "Skipped:         $totalSkipped" -ForegroundColor Yellow
Write-Host "Errors:          $totalErrors" -ForegroundColor $(if ($totalErrors -eq 0) { "Green" } else { "Red" })
Write-Host "Duration:        $totalDuration seconds`n" -ForegroundColor Gray

# Calculate pass rate
$passRate = if ($totalCollected -gt 0) { [math]::Round(($totalPassed / $totalCollected) * 100, 2) } else { 0 }
Write-Host "Pass Rate:       $passRate%" -ForegroundColor $(if ($passRate -ge 99) { "Green" } elseif ($passRate -ge 95) { "Yellow" } else { "Red" })

# Overall status
$overallSuccess = ($unitExitCode -eq 0) -and ($integrationExitCode -eq 0) -and ($totalFailed -eq 0) -and ($totalErrors -eq 0)

if ($overallSuccess) {
    Write-Host "`n[PASS] ALL TESTS PASSED" -ForegroundColor Green
} else {
    Write-Host "`n[FAIL] TEST FAILURES DETECTED" -ForegroundColor Red
    Write-Host "  Review logs in $resultsDir for details" -ForegroundColor Yellow
}

# Export structured results to JSON
$results = @{
    timestamp = $timestamp
    unit = @{
        total = $unitResults.Total
        passed = $unitResults.Passed
        failed = $unitResults.Failed
        skipped = $unitResults.Skipped
        errors = $unitResults.Errors
        duration = $unitResults.Duration
        exitCode = $unitExitCode
    }
    integration = @{
        total = $integrationResults.Total
        passed = $integrationResults.Passed
        failed = $integrationResults.Failed
        skipped = $integrationResults.Skipped
        errors = $integrationResults.Errors
        duration = $integrationResults.Duration
        exitCode = $integrationExitCode
    }
    overall = @{
        total = $totalCollected
        passed = $totalPassed
        failed = $totalFailed
        skipped = $totalSkipped
        errors = $totalErrors
        duration = $totalDuration
        passRate = $passRate
        success = $overallSuccess
    }
}

$jsonPath = Join-Path $resultsDir "test_results.json"
$results | ConvertTo-Json -Depth 3 | Out-File $jsonPath

Write-Host "`nResults exported to: $jsonPath" -ForegroundColor Cyan

# Return appropriate exit code
if ($overallSuccess) {
    exit 0
} else {
    exit 1
}
