param(
    [ValidateSet("bootstrap", "doctor", "ready", "serve", "acceptance", "validate")]
    [string]$Command = "ready",
    [string]$CorePath = "",
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8000
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    py -m venv .venv
}
if ($Command -eq "bootstrap") {
    if ($CorePath) { & $Python scripts/bootstrap.py --core-path $CorePath } else { & $Python scripts/bootstrap.py }
    exit $LASTEXITCODE
}
if (-not (Test-Path $Python)) { throw "Repository virtual environment is unavailable." }
switch ($Command) {
    "doctor" { & $Python -m aegis_os doctor }
    "ready" { & $Python -m aegis_os ready --host $HostAddress --port $Port }
    "serve" { & $Python -m aegis_os serve --host $HostAddress --port $Port }
    "acceptance" { & $Python scripts/release_acceptance.py }
    "validate" { & $Python scripts/validate.py }
}
exit $LASTEXITCODE
