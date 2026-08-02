param(
    [string]$CorePath = "..\aegis-core-clean",
    [string]$Output = ".\artifacts\operator-trial-report.json",
    [int]$Port = 8000,
    [string]$Bundle,
    [string]$Attestation,
    [string]$Signature,
    [string]$Policy,
    [string]$Ledger
)

$ErrorActionPreference = "Stop"
$Started = Get-Date

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    py -m venv .venv
}

$Python = ".\.venv\Scripts\python.exe"
& $Python "scripts\bootstrap.py" --core-path $CorePath --skip-tests

$Arguments = @("-m", "aegis_os", "operator-trial", "--port", "$Port", "--output", $Output, "--json")
if ($Bundle) {
    $Arguments += @("--bundle", $Bundle, "--attestation", $Attestation, "--signature", $Signature, "--policy", $Policy)
    if ($Ledger) { $Arguments += @("--ledger", $Ledger) }
}

& $Python @Arguments
if ($LASTEXITCODE -ne 0) { throw "AEGIS operator trial failed." }

& $Python -m pytest
if ($LASTEXITCODE -ne 0) { throw "AEGIS test suite failed." }

$Elapsed = (Get-Date) - $Started
Write-Host "Operator trial completed in $([math]::Round($Elapsed.TotalSeconds, 2)) seconds."
Write-Host "Audit report: $Output"
