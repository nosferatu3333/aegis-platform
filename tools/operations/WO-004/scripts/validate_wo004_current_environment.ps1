$ErrorActionPreference = "Stop"

$worktree = "$env:USERPROFILE\Projects\aegis-platform-wo-004"
$python = "$env:USERPROFILE\Projects\aegis-platform\env\Scripts\python.exe"
$branchExpected = "implementation/wo-004-kernel-convergence"
$baseExpected = "8514de1f4e1bafb73748ec74a9b29e8b2f83d952"

$expectedPaths = @(
    "aegis_os/core/kernel.py",
    "aegis_os/core/legacy_compatibility.py",
    "aegis_os/main.py",
    "docs/architecture/cognitive-pipeline.md",
    "tests/core/test_kernel.py"
)

$ruffPaths = @(
    "aegis_os/core/kernel.py",
    "aegis_os/core/cognitive_runtime.py",
    "aegis_os/core/legacy_compatibility.py",
    "aegis_os/main.py",
    "aegis_os/pipeline/composition.py",
    "tests/core/test_kernel.py",
    "tests/core/test_cognitive_runtime.py"
)

Write-Host "`n=== IDENTITY ==="

$branch = (git -C $worktree branch --show-current).Trim()
$head = (git -C $worktree rev-parse HEAD).Trim()

if ($branch -ne $branchExpected) {
    throw "Unexpected branch: $branch"
}

if ($head -ne $baseExpected) {
    throw "Unexpected base: $head"
}

Write-Host "Branch: $branch"
Write-Host "Head:   $head"

Write-Host "`n=== PATH BOUNDARY ==="

$statusLines = @(git -C $worktree status --short)
$changedPaths = @(
    $statusLines | ForEach-Object { $_.Substring(3) }
)

$unexpectedPaths = @(
    $changedPaths | Where-Object { $_ -notin $expectedPaths }
)

$missingPaths = @(
    $expectedPaths | Where-Object { $_ -notin $changedPaths }
)

if (
    $changedPaths.Count -ne 5 -or
    $unexpectedPaths.Count -gt 0 -or
    $missingPaths.Count -gt 0
) {
    Write-Host "Current status:"
    $statusLines
    throw "WO-004 changed-path boundary mismatch."
}

$statusLines
Write-Host "Path boundary: PASS"

Write-Host "`n=== WHITESPACE ==="

git -C $worktree diff --check

if ($LASTEXITCODE -ne 0) {
    throw "Tracked-file whitespace validation failed."
}

foreach ($relativePath in $expectedPaths) {
    $absolutePath = Join-Path $worktree $relativePath

    if (-not (Test-Path $absolutePath)) {
        throw "Missing file: $relativePath"
    }

    $trailingWhitespace = Select-String `
        -Path $absolutePath `
        -Pattern "[ `t]+$"

    if ($trailingWhitespace) {
        $trailingWhitespace
        throw "Trailing whitespace found in $relativePath."
    }
}

Write-Host "Whitespace: PASS"

Write-Host "`n=== PYTHON ENVIRONMENT ==="

if (-not (Test-Path $python)) {
    throw "Shared Python environment was not found."
}

& $python --version
& $python -m pytest --version
& $python -m ruff --version

$env:PYTHONDONTWRITEBYTECODE = "1"

Push-Location $worktree

try {
    Write-Host "`n=== FOCUSED TESTS ==="

    & $python -m pytest `
        -p no:cacheprovider `
        -q `
        tests/core/test_kernel.py `
        tests/core/test_cognitive_runtime.py `
        tests/api/test_execute_task.py `
        tests/benchmark/test_runner.py `
        test_agent_cognitive_loop.py

    if ($LASTEXITCODE -ne 0) {
        throw "Focused tests failed."
    }

    Write-Host "`n=== FULL TEST SUITE ==="

    & $python -m pytest `
        -p no:cacheprovider `
        -q

    if ($LASTEXITCODE -ne 0) {
        throw "Full test suite failed."
    }

    Write-Host "`n=== RUFF LINT ==="

    & $python -m ruff check @ruffPaths

    if ($LASTEXITCODE -ne 0) {
        throw "Ruff lint failed."
    }

    Write-Host "`n=== RUFF FORMAT CHECK ==="

    & $python -m ruff format --check @ruffPaths

    if ($LASTEXITCODE -ne 0) {
        throw "Ruff format check failed."
    }

    Write-Host "`n=== DEPENDENCY INTEGRITY ==="

    & $python -m pip check

    if ($LASTEXITCODE -ne 0) {
        throw "Dependency integrity failed."
    }
}
finally {
    Pop-Location
}

Write-Host "`n=== PYTHON 3.11 AVAILABILITY ==="

$python311Available = $false

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.11 --version 2>$null

    if ($LASTEXITCODE -eq 0) {
        $python311Available = $true
    }
}

if ($python311Available) {
    Write-Host "Python 3.11 interpreter: AVAILABLE"
}
else {
    Write-Host "Python 3.11 interpreter: NOT DETECTED"
    Write-Host "This does not invalidate the current Python 3.14 validation,"
    Write-Host "but the separate Python 3.11 governance gate remains pending."
}

Write-Host "`n=== FINAL PRESERVATION ==="

$finalStatus = @(git -C $worktree status --short)
$finalPaths = @(
    $finalStatus | ForEach-Object { $_.Substring(3) }
)

if (
    $finalPaths.Count -ne 5 -or
    @($finalPaths | Where-Object { $_ -notin $expectedPaths }).Count -gt 0
) {
    $finalStatus
    throw "Validation produced an unexpected repository change."
}

[pscustomobject]@{
    Branch             = $branch
    Head               = $head
    ChangedPathCount   = $finalPaths.Count
    CurrentPythonGate  = "PASS"
    Python311Available = $python311Available
    WorktreeBoundary   = "PASS"
} | Format-List

Write-Host "`n=== FINAL STATUS ==="
$finalStatus

Write-Host "`nWO-004 CURRENT-ENV VALIDATION: PASS"
