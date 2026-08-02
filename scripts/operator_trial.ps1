param(
    [string]$CorePath = "..\aegis-core-clean",
    [string]$Output = ".\artifacts\operator-trial-report.json",
    [int]$Port = 8000,
    [string]$Bundle,
    [string]$Attestation,
    [string]$Signature,
    [string]$Policy,
    [string]$PublicKey,
    [string]$Ledger
)

$ErrorActionPreference = "Stop"
$Started = Get-Date

function Write-FailureReport {
    param([string]$Stage, [string]$Message)
    $Directory = Split-Path -Parent $Output
    if ($Directory) { New-Item -ItemType Directory -Force $Directory | Out-Null }
    $Payload = [ordered]@{
        schema_version = "1.0"
        platform_version = "1.6.0"
        overall_status = "failed"
        failed_stage = $Stage
        error = $Message
        started_at = $Started.ToString("o")
        finished_at = (Get-Date).ToString("o")
        recovery_commands = @(
            "python -m pip install -r requirements/release.txt",
            "python -m pip check",
            "python -m aegis_os doctor"
        )
    }
    $Payload | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $Output
}

try {
    if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
        py -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed." }
    }

    $Python = ".\.venv\Scripts\python.exe"
    & $Python "scripts\bootstrap.py" --core-path $CorePath --skip-tests
    if ($LASTEXITCODE -ne 0) { throw "Bootstrap failed with exit code $LASTEXITCODE." }

    $TemporaryPolicy = $null
    if ($Bundle -and -not $Policy -and $PublicKey) {
        $TemporaryPolicy = Join-Path ([System.IO.Path]::GetTempPath()) ("aegis-trial-policy-" + [guid]::NewGuid().ToString("N") + ".json")
        & $Python -m aegis_os trust-init --public-key $PublicKey --policy $TemporaryPolicy
        if ($LASTEXITCODE -ne 0) { throw "Temporary trust-policy initialization failed." }
        $Policy = $TemporaryPolicy
    }

    $Arguments = @("-m", "aegis_os", "operator-trial", "--port", "$Port", "--output", $Output, "--json")
    if ($Bundle) {
        if (-not ($Attestation -and $Signature -and $Policy)) {
            throw "Bundle verification requires Attestation, Signature, and Policy or PublicKey."
        }
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
}
catch {
    Write-FailureReport -Stage "operator-trial-wrapper" -Message $_.Exception.Message
    Write-Host "Partial failure report: $Output"
    throw
}
finally {
    if ($TemporaryPolicy -and (Test-Path $TemporaryPolicy)) {
        Remove-Item $TemporaryPolicy -Force -ErrorAction SilentlyContinue
    }
}
