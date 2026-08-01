$ErrorActionPreference = "Stop"

$worktree = "$env:USERPROFILE\Projects\aegis-platform-wo-004-governance"
$base = "8514de1f4e1bafb73748ec74a9b29e8b2f83d952"

$workOrderRelative = "governance/work-orders/WO-004_KERNEL_CANONICAL_RUNTIME_CONVERGENCE.md"
$traceRelative = "governance/TRACEABILITY.md"

$workOrderPath = Join-Path $worktree $workOrderRelative
$tracePath = Join-Path $worktree $traceRelative
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

Write-Host "`n=== PREFLIGHT ==="

if (-not (Test-Path $worktree)) {
    throw "WO-004 governance worktree does not exist."
}

$actualHead = (git -C $worktree rev-parse HEAD).Trim()
$actualBranch = (git -C $worktree branch --show-current).Trim()
$initialStatus = @(git -C $worktree status --short)

if ($actualHead -ne $base) {
    throw "WO-004 governance base mismatch."
}

if ($actualBranch -ne "governance/wo-004-kernel-convergence") {
    throw "WO-004 governance branch mismatch."
}

if ($initialStatus.Count -ne 0) {
    throw "WO-004 governance worktree is not clean."
}

if (Test-Path $workOrderPath) {
    throw "WO-004 work-order file already exists."
}

$currentTraceability = [System.IO.File]::ReadAllText($tracePath)

if ($currentTraceability -match "(?m)^### TR-006:") {
    throw "TR-006 already exists."
}

Write-Host "Preflight: PASS"

$workOrder = @'
# Work Order WO-004: Kernel Canonical Runtime Convergence

**Status:** ACTIVE — IMPLEMENTATION AUTHORIZED  
**Authority:** Product Owner / Founder activation decision, recorded by Documentation & Governance  
**Date authorized:** 2026-07-31  
**Authoritative base:** `8514de1f4e1bafb73748ec74a9b29e8b2f83d952`  
**Implementation owner:** Implementation Engineer  
**Required review owners:** QA & Verification; Architecture Auditor; Documentation & Governance  
**Integration authority:** NOT GRANTED  
**Remote-publication authority:** NOT GRANTED  
**Governed by:** `governance/ENGINEERING_CHARTER.md`

---

## Objective

Converge the application entry path onto the canonical `CognitiveRuntime` while preserving the existing legacy cognitive-loop contract behind an explicit compatibility adapter.

The intended direction is:

```text
aegis_os.main
→ Kernel
→ canonical CognitiveRuntime
→ canonical pipeline
→ optional simulated execution
```

The temporary compatibility direction is:

```text
legacy caller
→ Kernel.process_goal()
→ explicit legacy compatibility adapter
→ CognitiveRuntime.process_goal()
→ legacy CognitiveOrchestrator
```

The canonical path must become the normal application path. The legacy path must remain available only as an explicit compatibility boundary.

## Authorization Basis

The current repository contains two runtime entry paths:

1. The canonical typed path exposed through `CognitiveRuntime.run()` and `CognitiveRuntime.process()`.
2. The historical path exposed through `CognitiveRuntime.process_goal()` and the legacy `CognitiveOrchestrator`.

`aegis_os.pipeline.composition.create_default_runtime()` already constructs the canonical pipeline and runtime used by the API and benchmark suite.

`Kernel` currently constructs `CognitiveRuntime()` directly without the canonical pipeline and exposes only `process_goal()` as its processing method.

`aegis_os.main` therefore still enters the historical cognitive loop rather than the canonical runtime.

WO-004 authorizes only the bounded convergence required to correct this entry-path split.

## Authoritative Base

Implementation must begin from exactly:

```text
8514de1f4e1bafb73748ec74a9b29e8b2f83d952
Integrate governance records onto main lineage
```

No earlier branch, preserved implementation branch, stash, rejected candidate, or divergent governance lineage is an authorized base.

## Authorized Implementation File List

Only the following implementation, test, and architecture-documentation paths may differ from the authoritative base in a WO-004 candidate.

### Kernel and Runtime

- `aegis_os/core/kernel.py`
- `aegis_os/core/cognitive_runtime.py`
- `aegis_os/core/legacy_compatibility.py` — new file

### Composition and Entry Point

- `aegis_os/pipeline/composition.py`
- `aegis_os/main.py`

### Tests

- `tests/core/test_kernel.py` — new file
- `tests/core/test_cognitive_runtime.py`

### Architecture Documentation

- `docs/architecture/cognitive-pipeline.md`

Any implementation change outside this exact list requires a formal governance amendment before the change is made.

## Governance Record Paths

Documentation & Governance may modify only these governance paths for WO-004 authorization and later disposition records:

- `governance/TRACEABILITY.md`
- `governance/work-orders/WO-004_KERNEL_CANONICAL_RUNTIME_CONVERGENCE.md`

These governance paths are not part of the implementation candidate allowlist.

## Locked Architectural Decisions

1. `Kernel` becomes a canonical-runtime entry boundary.
2. The normal `Kernel` processing path must call the typed canonical runtime.
3. The canonical Kernel method must accept a task, a request identifier, and an explicit execution choice.
4. The canonical Kernel method must return a `CanonicalRuntimeResult`.
5. The canonical pipeline must be configured through the existing composition root rather than duplicated inside `Kernel`.
6. `Kernel.process_goal()` remains temporarily available for backward compatibility.
7. `Kernel.process_goal()` must delegate through an explicit compatibility adapter.
8. The compatibility adapter must contain delegation and lifecycle compatibility only.
9. The compatibility adapter must not implement planning, execution, validation, evaluation, governance, learning, or persistence logic.
10. The legacy `CognitiveOrchestrator` must not become part of the canonical path.
11. The canonical runtime remains the owner of canonical analysis, simulated execution, conformance validation, and result construction.
12. The existing typed runtime contracts and schema version remain unchanged unless a formal amendment explicitly authorizes a change.
13. `aegis_os.main` must use the canonical Kernel path rather than `process_goal()`.
14. The main demonstration must print a serializable canonical result.
15. Only simulated execution is permitted.
16. The API and benchmark composition must not regress.
17. The legacy orchestrator must not be deleted under WO-004.
18. Compatibility preservation does not authorize indefinite duplication; removal of the compatibility path requires a separate work order.

## Required Compatibility Guarantees

- Direct canonical-runtime behavior remains compatible.
- Existing API behavior remains compatible.
- Existing benchmark behavior remains compatible.
- `CognitiveRuntime.process_goal()` remains available during this work order.
- Existing legacy compatibility tests continue to pass.
- `Kernel.process_goal()` remains callable but is visibly separated from the canonical path.
- Existing request-correlation and conformance invariants remain unchanged.
- No real or external execution is introduced.
- No public endpoint is added, removed, or renamed.

## Explicit Non-Goals and Exclusions

WO-004 does not authorize:

- Deletion of `CognitiveOrchestrator`.
- Reimplementation of the cognitive pipeline.
- Changes to intent analysis or agent selection.
- Changes to execution semantics.
- Real execution or external actions.
- Governance execution.
- Evaluation or scoring implementation.
- Learning or memory expansion.
- Persistence changes.
- New API endpoints.
- Dashboard changes.
- Benchmark redesign.
- Schema-version changes.
- Provider or model integration.
- Dependency changes.
- CI or workflow changes.
- Repository cleanup.
- Ruleset or branch-protection changes.
- Tag creation or mutation.
- Modification of `main`.
- Push, merge, release, deployment, or publication.
- Any path outside the exact authorized file lists.

## Acceptance Criteria

A WO-004 implementation candidate is eligible for review only when all of the following are true:

1. The candidate descends from the exact authoritative base.
2. Only authorized implementation paths differ from the base.
3. `Kernel` exposes a canonical typed processing method.
4. The canonical Kernel method delegates to `CognitiveRuntime.run()` or the equivalent typed canonical boundary.
5. The canonical Kernel method returns `CanonicalRuntimeResult`.
6. Default application composition provides a configured canonical pipeline.
7. `aegis_os.main` no longer calls `Kernel.process_goal()`.
8. `aegis_os.main` produces a serializable canonical payload.
9. `Kernel.process_goal()` delegates through the explicit compatibility adapter.
10. The compatibility adapter preserves the established legacy result behavior.
11. The compatibility adapter introduces no independent cognitive or execution logic.
12. Existing canonical-runtime tests pass.
13. New Kernel tests cover canonical routing, request-ID preservation, analysis-only behavior, simulated-execution routing, legacy compatibility routing, lifecycle behavior, and dependency injection.
14. Existing API tests pass.
15. Existing benchmark tests pass.
16. The full repository test suite passes.
17. Ruff lint passes for all authorized Python paths.
18. Ruff formatting validation passes for all authorized Python paths.
19. Repository validation and dependency-integrity checks pass.
20. `git diff --check` passes.
21. The candidate worktree is clean.
22. No unauthorized file, commit ancestry, tag, branch, or remote reference is changed.

## Required Validation Evidence

The Implementation Engineer must provide evidence tied to one exact proposed candidate SHA:

- Candidate SHA and tree.
- Parent SHA.
- Exact changed-path list.
- Base-to-candidate ancestry proof.
- Focused Kernel and canonical-runtime tests.
- Existing API tests.
- Existing benchmark tests.
- Full repository test suite.
- Python 3.11 minimum-version evidence.
- Ruff lint.
- Ruff formatting check.
- Repository validation.
- Dependency integrity.
- Whitespace validation.
- Clean-state verification.
- Confirmation that no remote mutation occurred.
- Confirmation that `main`, tags, rulesets, and unrelated worktrees remained unchanged.

## Review Sequence

1. The Implementation Engineer constructs and validates a bounded implementation branch.
2. Release & Integration may freeze one immutable candidate only under separate candidate-designation authority.
3. QA & Verification evaluates the exact immutable candidate SHA.
4. The Architecture Auditor evaluates the same immutable candidate SHA after QA.
5. Documentation & Governance reconciles scope, evidence, findings, and review verdicts.
6. Any correction requires a new commit and a new candidate designation.
7. Integration into `main` requires a separate explicit authorization.
8. Remote publication requires a separate explicit authorization.

## Stop Conditions

Implementation and review must stop if:

- the base identity differs;
- an unauthorized path changes;
- canonical API or benchmark behavior regresses;
- real execution is introduced;
- the compatibility adapter acquires independent orchestration logic;
- the candidate changes during review;
- required validation cannot be reproduced;
- `main`, a tag, a ruleset, or a remote reference changes without separate authority.

## Current Disposition

```text
WO-004: ACTIVE — IMPLEMENTATION AUTHORIZED
Authoritative base: 8514de1f4e1bafb73748ec74a9b29e8b2f83d952
Implementation scope: BOUNDED
Candidate designated: NO
QA review: NOT STARTED
Architecture review: NOT STARTED
Integration authority: NOT GRANTED
Publication authority: NOT GRANTED
```
'@

$traceEntry = @'
### TR-006: Kernel Canonical Runtime Convergence

**Status:** Active — Implementation Authorized  
**Recorded:** 2026-07-31  
**Subject:** Convergence of the Kernel and application entry point onto the canonical runtime

| Sequence | Record | Relationship | Repository reference |
|---|---|---|---|
| 1 | WO-002 Closure Direction | Recorded the future Phase I convergence direction `main → Kernel → explicit legacy compatibility adapter → canonical CognitiveRuntime` without implementation authority. | [`work-orders/WO-002_CANONICAL_RUNTIME_CONTRACT_HARDENING.md`](work-orders/WO-002_CANONICAL_RUNTIME_CONTRACT_HARDENING.md) |
| 2 | WO-003 Explicit Exclusion | Confirmed that Kernel/main convergence was outside WO-003 and required a separate authorization boundary. | [`work-orders/WO-003_RUNTIME_EXECUTION_CONFORMANCE_VALIDATION.md`](work-orders/WO-003_RUNTIME_EXECUTION_CONFORMANCE_VALIDATION.md) |
| 3 | Main-Integrity Governance Closure | Closed the repository-protection work and preserved WO-004 as not activated pending a separate Product Owner decision. | [`AEGIS_MAIN_BRANCH_PROTECTION_GOVERNANCE_CLOSURE.md`](AEGIS_MAIN_BRANCH_PROTECTION_GOVERNANCE_CLOSURE.md) |
| 4 | Product Owner / Founder Activation | Explicitly approved activation of WO-004 for bounded Kernel canonical-runtime convergence. | Decision received 2026-07-31 |
| 5 | Work Order — Kernel Canonical Runtime Convergence | Defines the exact base, implementation allowlist, architectural decisions, compatibility guarantees, exclusions, acceptance criteria, validation evidence, review sequence, and authority boundaries. | [`work-orders/WO-004_KERNEL_CANONICAL_RUNTIME_CONVERGENCE.md`](work-orders/WO-004_KERNEL_CANONICAL_RUNTIME_CONVERGENCE.md) |

#### Current Governance State

| Control | Status |
|---|---|
| Work order | `WO-004` |
| Work-order status | **ACTIVE — IMPLEMENTATION AUTHORIZED** |
| Authoritative base | `8514de1f4e1bafb73748ec74a9b29e8b2f83d952` |
| Implementation boundary | **EXACT EIGHT-PATH ALLOWLIST** |
| Canonical Kernel path | **AUTHORIZED FOR IMPLEMENTATION** |
| Explicit legacy adapter | **REQUIRED** |
| Legacy compatibility | **TEMPORARILY REQUIRED** |
| Candidate | **NOT DESIGNATED** |
| QA & Verification | **NOT STARTED** |
| Architecture Auditor | **NOT STARTED** |
| Integration authority | **NOT GRANTED** |
| Remote-publication authority | **NOT GRANTED** |
| Next eligible owner | **Implementation Engineer** |

#### Authorization Boundary

WO-004 authorizes bounded local implementation only from the exact authoritative base.

No candidate designation, tag, merge, local-main update, remote publication, release, deployment, ruleset change, repository cleanup, or destructive operation is authorized by this traceability entry.

Implementation must remain inside the exact allowlist and preserve the typed canonical runtime, API behavior, benchmark behavior, request correlation, simulation boundary, and temporary legacy compatibility contract.

Final governance state:

`WO-004 ACTIVE — BOUNDED IMPLEMENTATION AUTHORIZED`
'@

$workOrder = $workOrder -replace "`r`n", "`n"
$traceEntry = $traceEntry -replace "`r`n", "`n"

[System.IO.File]::WriteAllText($workOrderPath, $workOrder + "`n", $utf8NoBom)

if (-not $currentTraceability.EndsWith("`n")) {
    $currentTraceability += "`n"
}

[System.IO.File]::WriteAllText(
    $tracePath,
    $currentTraceability + "`n" + $traceEntry + "`n",
    $utf8NoBom
)

Write-Host "`n=== VALIDATION ==="

$changedPaths = @(
    git -C $worktree status --short |
        ForEach-Object { $_.Substring(3) }
)

$expectedPaths = @(
    $traceRelative,
    $workOrderRelative
)

$unexpectedPaths = @(
    $changedPaths | Where-Object { $_ -notin $expectedPaths }
)

if ($changedPaths.Count -ne 2) {
    throw "Expected exactly two changed governance paths; found $($changedPaths.Count)."
}

if ($unexpectedPaths.Count -gt 0) {
    throw "Unexpected path detected: $($unexpectedPaths -join ', ')"
}

git -C $worktree diff --check

if ($LASTEXITCODE -ne 0) {
    throw "Governance content failed whitespace validation."
}

[pscustomobject]@{
    Branch              = (git -C $worktree branch --show-current).Trim()
    Head                = (git -C $worktree rev-parse HEAD).Trim()
    ChangedPathCount    = $changedPaths.Count
    UnexpectedPathCount = $unexpectedPaths.Count
    WorkOrderExists     = Test-Path $workOrderPath
    TraceEntryExists    = (
        [System.IO.File]::ReadAllText($tracePath) -match
        "(?m)^### TR-006: Kernel Canonical Runtime Convergence$"
    )
} | Format-List

Write-Host "`n=== STATUS ==="
git -C $worktree status --short

Write-Host "`n=== DIFF STAT ==="
git -C $worktree diff --stat

Write-Host "`nWO-004 GOVERNANCE DRAFT: READY FOR REVIEW"
