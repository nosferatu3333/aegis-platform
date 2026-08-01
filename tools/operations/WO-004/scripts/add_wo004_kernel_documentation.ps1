$ErrorActionPreference = "Stop"

$worktree = "$env:USERPROFILE\Projects\aegis-platform-wo-004"
$docPath = Join-Path $worktree "docs/architecture/cognitive-pipeline.md"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

Write-Host "`n=== PREFLIGHT ==="

if (-not (Test-Path $docPath)) {
    throw "Le document d'architecture est introuvable."
}

$document = [System.IO.File]::ReadAllText($docPath)
$document = $document -replace "`r`n", "`n"

if ($document -match "(?m)^## Kernel entry boundary$") {
    Write-Host "La section existe deja."
}
else {
    $section = @'

## Kernel entry boundary

`Kernel` is the canonical application entry boundary. Its default construction
uses `aegis_os.pipeline.composition.create_default_runtime()` rather than
duplicating pipeline composition inside the Kernel.

The canonical path is:

```text
caller
  -> Kernel.process_task(task, request_id, execute)
  -> CognitiveRuntime.run(...)
  -> CognitiveRequestPipeline
  -> optional simulated execution
  -> execution-conformance validation
  -> CanonicalRuntimeResult
```

`Kernel.boot()` starts only the canonical runtime. The application entry point
in `aegis_os.main` uses `Kernel.process_task()` and serializes the canonical
result through `CanonicalRuntimeResult.to_dict()`.

The historical `Kernel.process_goal()` contract remains temporarily available
through `LegacyCompatibilityAdapter`. The legacy runtime is constructed and
started lazily only when a legacy goal is submitted:

```text
legacy caller
  -> Kernel.process_goal(goal)
  -> LegacyCompatibilityAdapter
  -> CognitiveRuntime.process_goal(goal)
  -> CognitiveOrchestrator
```

The compatibility adapter contains lifecycle and delegation behavior only. It
does not implement analysis, planning, execution, validation, governance,
evaluation, learning, or persistence. The legacy orchestrator is not part of
the canonical Kernel path.

The API and benchmark suite continue to use the shared composition root
directly, preserving their established behavior.
'@

    $updatedDocument = $document.TrimEnd() + $section + "`n"

    [System.IO.File]::WriteAllText(
        $docPath,
        $updatedDocument,
        $utf8NoBom
    )
}

Write-Host "`n=== SECTION EXISTS ==="

$sectionExists = Select-String `
    -Path $docPath `
    -Pattern "^## Kernel entry boundary$" `
    -Quiet

Write-Host $sectionExists

if (-not $sectionExists) {
    throw "La section n'a pas ete ajoutee."
}

Write-Host "`n=== STATUS ==="
git -C $worktree status --short

Write-Host "`n=== DIFF CHECK ==="
git -C $worktree diff --check

if ($LASTEXITCODE -ne 0) {
    throw "La validation des espaces a echoue."
}

Write-Host "`n=== DIFF STAT ==="
git -C $worktree diff --stat

Write-Host "`nWO-004 DOCUMENTATION: PASS"
