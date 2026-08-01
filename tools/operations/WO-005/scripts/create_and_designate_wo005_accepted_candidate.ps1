$ErrorActionPreference = "Stop"

if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$repo = "$env:USERPROFILE\Projects\aegis-platform"

$architecturalBase = "be7502f73b51808d54728f912ead46ad0073c7b9"
$governanceMain = "ad743b4568bbd82527f7ff192c5b10ca4d59c2e9"

$candidateWorktree = "$env:USERPROFILE\Projects\aegis-platform-wo-005-accepted-candidate"
$candidateBranch = "documentation/wo-005-accepted-environment-interaction-design"
$candidateSubject = "Accept WO-005 environment interaction design"

$reviewWorktree = "$env:USERPROFILE\Projects\aegis-platform-wo-005-candidate-review"
$reviewBranch = "governance/wo-005-accepted-candidate-designation"
$designationSubject = "Designate WO-005 accepted design candidate"

$adrRelative = "docs/adr/ADR-006-environment-interaction-layer.md"
$architectureRelative = "docs/architecture/environment-interaction-layer.md"
$specRelative = "docs/specifications/v0.5-phase-b-environment-interaction-layer.md"
$roadmapRelative = "docs/roadmap/ROADMAP.md"

$workOrderRelative = "governance/work-orders/WO-005_ENVIRONMENT_INTERACTION_LAYER_SPECIFICATION.md"
$traceabilityRelative = "governance/TRACEABILITY.md"

$deliverablePaths = @(
    $adrRelative,
    $architectureRelative,
    $specRelative,
    $roadmapRelative
)

$governancePaths = @(
    $traceabilityRelative,
    $workOrderRelative
)

$operationsRoot = [Environment]::GetEnvironmentVariable(
    "AEGIS_OPERATIONS",
    "User"
)

if ([string]::IsNullOrWhiteSpace($operationsRoot)) {
    $operationsRoot = "$env:USERPROFILE\Projects\AEGIS-operations"
}

$logDirectory = Join-Path $operationsRoot "logs\WO-005"
$manifestPath = Join-Path $logDirectory "WO-005-accepted-candidate-designation.txt"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Invoke-Native {
    param(
        [scriptblock]$Command,
        [string]$Label
    )

    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    try {
        & $Command
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedPreference
    }

    if ($exitCode -ne 0) {
        throw "$Label failed with exit code $exitCode."
    }
}

function Get-LiveRemoteMain {
    param([string]$Repository)

    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    try {
        $lines = @(
            & git -C $Repository ls-remote --heads origin refs/heads/main
        )
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedPreference
    }

    if ($exitCode -ne 0) {
        throw "Unable to read live remote main."
    }

    if ($lines.Count -ne 1) {
        throw "Expected exactly one live remote main reference."
    }

    return (($lines[0] -split "\s+")[0]).Trim()
}

function Get-RegisteredWorktrees {
    param([string]$Repository)

    $items = @()
    $currentPath = $null
    $currentBranch = $null

    foreach ($line in @(git -C $Repository worktree list --porcelain)) {
        if ($line -like "worktree *") {
            if ($currentPath) {
                $items += [pscustomobject]@{
                    Path = $currentPath
                    Branch = $currentBranch
                }
            }

            $currentPath = $line.Substring(9)
            $currentBranch = $null
        }
        elseif ($line -like "branch *") {
            $currentBranch = $line.Substring(7)
        }
        elseif ([string]::IsNullOrWhiteSpace($line) -and $currentPath) {
            $items += [pscustomobject]@{
                Path = $currentPath
                Branch = $currentBranch
            }

            $currentPath = $null
            $currentBranch = $null
        }
    }

    if ($currentPath) {
        $items += [pscustomobject]@{
            Path = $currentPath
            Branch = $currentBranch
        }
    }

    return @($items)
}

function Assert-AllWorktreesClean {
    param(
        [string]$Repository,
        [string]$Label
    )

    foreach ($item in @(Get-RegisteredWorktrees $Repository)) {
        if (-not (Test-Path -LiteralPath $item.Path)) {
            throw "$Label registered worktree path is unavailable: $($item.Path)"
        }

        if (@(git -C $item.Path status --short).Count -ne 0) {
            throw "$Label dirty worktree: $($item.Path)"
        }
    }
}

function Assert-ExactPathSet {
    param(
        [string[]]$Actual,
        [string[]]$Expected,
        [string]$Label
    )

    $actualSorted = @($Actual | Sort-Object -Unique)
    $expectedSorted = @($Expected | Sort-Object -Unique)

    $unexpected = @(
        $actualSorted |
            Where-Object { $_ -notin $expectedSorted }
    )

    $missing = @(
        $expectedSorted |
            Where-Object { $_ -notin $actualSorted }
    )

    if (
        $actualSorted.Count -ne $expectedSorted.Count -or
        $unexpected.Count -gt 0 -or
        $missing.Count -gt 0
    ) {
        Write-Host "$Label actual paths:"
        $actualSorted | ForEach-Object { Write-Host " - $_" }

        if ($unexpected.Count -gt 0) {
            Write-Host "Unexpected paths:"
            $unexpected | ForEach-Object { Write-Host " - $_" }
        }

        if ($missing.Count -gt 0) {
            Write-Host "Missing paths:"
            $missing | ForEach-Object { Write-Host " - $_" }
        }

        throw "$Label path boundary mismatch."
    }
}

function Replace-ExactlyOnce {
    param(
        [string]$Text,
        [string]$OldValue,
        [string]$NewValue,
        [string]$Label
    )

    $first = $Text.IndexOf(
        $OldValue,
        [System.StringComparison]::Ordinal
    )

    if ($first -lt 0) {
        throw "Required text was not found for $Label."
    }

    $second = $Text.IndexOf(
        $OldValue,
        $first + $OldValue.Length,
        [System.StringComparison]::Ordinal
    )

    if ($second -ge 0) {
        throw "Required text occurs more than once for $Label."
    }

    return $Text.Substring(0, $first) +
        $NewValue +
        $Text.Substring($first + $OldValue.Length)
}

function Assert-ContainsAll {
    param(
        [string]$Text,
        [string[]]$Required,
        [string]$Label
    )

    foreach ($requiredText in $Required) {
        if (-not $Text.Contains($requiredText)) {
            throw "$Label is missing required text: $requiredText"
        }
    }
}

Write-Host "`n=== WO-005 ACCEPTED CANDIDATE PREFLIGHT ==="

if (-not (Test-Path -LiteralPath $repo)) {
    throw "Repository not found: $repo"
}

Invoke-Native {
    git -C $repo fetch origin `
        "+refs/heads/main:refs/remotes/origin/main"
} "Remote main refresh"

$localMainBefore = (
    git -C $repo rev-parse refs/heads/main
).Trim()

$originMainBefore = (
    git -C $repo rev-parse refs/remotes/origin/main
).Trim()

$liveMainBefore = Get-LiveRemoteMain $repo

foreach ($identity in @(
    $localMainBefore,
    $originMainBefore,
    $liveMainBefore
)) {
    if ($identity -ne $governanceMain) {
        throw "Main identity differs from the published WO-005 governance amendment."
    }
}

Assert-AllWorktreesClean `
    -Repository $repo `
    -Label "Preflight"

foreach ($path in $deliverablePaths) {
    $found = @(
        git -C $repo ls-tree `
            -r `
            --name-only `
            $architecturalBase `
            -- `
            $path
    )

    if (
        $LASTEXITCODE -ne 0 -or
        $found.Count -ne 1 -or
        $found[0] -ne $path
    ) {
        throw "Required pre-existing deliverable document is missing at the architectural base: $path"
    }
}

if (Test-Path -LiteralPath $candidateWorktree) {
    throw "Candidate worktree already exists: $candidateWorktree"
}

if (@(git -C $repo branch --list $candidateBranch).Count -ne 0) {
    throw "Candidate branch already exists: $candidateBranch"
}

if (Test-Path -LiteralPath $reviewWorktree) {
    throw "Candidate-review worktree already exists: $reviewWorktree"
}

if (@(git -C $repo branch --list $reviewBranch).Count -ne 0) {
    throw "Candidate-review branch already exists: $reviewBranch"
}

Write-Host "Main identity, clean-state, and four pre-existing documents: PASS"

Write-Host "`n=== CREATE CANONICAL DOCUMENT CANDIDATE ==="

Invoke-Native {
    git -C $repo worktree add `
        -b $candidateBranch `
        $candidateWorktree `
        $architecturalBase
} "WO-005 candidate worktree creation"

$adrPath = Join-Path $candidateWorktree $adrRelative
$architecturePath = Join-Path $candidateWorktree $architectureRelative
$specPath = Join-Path $candidateWorktree $specRelative
$roadmapPath = Join-Path $candidateWorktree $roadmapRelative

try {
    Write-Host "`n=== ACCEPT ADR-006 ==="

    $adr = [System.IO.File]::ReadAllText($adrPath)
    $adr = $adr -replace "`r`n", "`n"

    if ($adr.Contains("## WO-005 acceptance record")) {
        throw "ADR-006 already contains a WO-005 acceptance record."
    }

    $adr = Replace-ExactlyOnce `
        -Text $adr `
        -OldValue "- **Status:** Proposed" `
        -NewValue "- **Status:** Accepted" `
        -Label "ADR-006 status"

    $adrAcceptance = @'

## WO-005 acceptance record

- Acceptance date: 2026-07-31
- Governing work order: `WO-005`
- Architectural base: `be7502f73b51808d54728f912ead46ad0073c7b9`
- Governance amendment main: `ad743b4568bbd82527f7ff192c5b10ca4d59c2e9`
- Accepted scope: provider-neutral, deterministic, simulation-only Phase B design
- Runtime implementation: not included
- Live providers, credentials, persistence, and external I/O: not authorized

Architecture, specification, and roadmap reconciliation confirm that Phase B
remains isolated from the current cognitive pipeline, execution engine, API,
dashboard, and benchmark fixtures.

The accepted implementation contract is the existing
[`v0.5 Phase B — Environment Interaction Layer implementation specification`](../specifications/v0.5-phase-b-environment-interaction-layer.md).

Acceptance of this ADR does not authorize implementation, integration,
publication of this candidate, live execution, provider access, tagging,
release creation, ruleset modification, or cleanup.
'@

    [System.IO.File]::WriteAllText(
        $adrPath,
        $adr.TrimEnd() + $adrAcceptance + "`n",
        $utf8NoBom
    )

    Write-Host "ADR-006 accepted: PASS"

    Write-Host "`n=== RECONCILE ACCEPTED ARCHITECTURE ==="

    $architecture = [System.IO.File]::ReadAllText($architecturePath)
    $architecture = $architecture -replace "`r`n", "`n"

    if ($architecture.Contains("## WO-005 accepted-design handoff")) {
        throw "Architecture already contains the WO-005 accepted-design handoff."
    }

    $oldArchitectureStatus = @'
> **Status: Proposed architecture.** This document is the current architecture
> authority for Phase B. It designs a simulation-first boundary; it does not
> describe implemented environment runtime behavior.
'@

    $newArchitectureStatus = @'
> **Status: Accepted architecture; runtime not implemented.** This document is
> the current architecture authority for Phase B. It defines a
> simulation-first boundary; it does not describe implemented environment
> runtime behavior.
'@

    $architecture = Replace-ExactlyOnce `
        -Text $architecture `
        -OldValue $oldArchitectureStatus `
        -NewValue $newArchitectureStatus `
        -Label "architecture status"

    $architectureAcceptance = @'

## WO-005 accepted-design handoff

WO-005 accepts this architecture together with ADR-006 and the existing
[Phase B implementation specification](../specifications/v0.5-phase-b-environment-interaction-layer.md).

The first runtime increment remains bounded to explicit immutable contracts,
instance-owned registration, deterministic resolution, simulation-only policy,
separate approval evaluation, deterministic simulated adapters, normalized
results, immutable receipts, and focused in-memory tests.

The accepted design preserves these ownership boundaries:

- Phase A owns resource requirements, catalog state, and resource resolution;
- Phase B consumes one resolved `ResourceReference` without re-resolving it;
- policy and approval precede adapter invocation;
- adapters declare support but never authorize or approve themselves;
- `LIVE` is modeled only for explicit rejection in this increment;
- provider clients, credentials, external I/O, persistence, observations,
  memory, learning, and current execution integration remain deferred.

The existing implementation specification is accepted through bounded revision,
not replaced. Runtime code and test creation require a later separately
authorized work order using the exact specification package and test boundary.
'@

    [System.IO.File]::WriteAllText(
        $architecturePath,
        $architecture.TrimEnd() + $architectureAcceptance + "`n",
        $utf8NoBom
    )

    Write-Host "Architecture accepted and reconciled: PASS"

    Write-Host "`n=== ACCEPT PRE-EXISTING IMPLEMENTATION SPECIFICATION ==="

    $spec = [System.IO.File]::ReadAllText($specPath)
    $spec = $spec -replace "`r`n", "`n"

    if ($spec.Contains("## WO-005 acceptance and governance boundary")) {
        throw "Specification already contains the WO-005 acceptance section."
    }

    Assert-ContainsAll `
        -Text $spec `
        -Required @(
            "- **Status:** Proposed implementation specification",
            "- **Decision record:** [ADR-006](../adr/ADR-006-environment-interaction-layer.md), Proposed",
            "## 3. Package structure",
            "aegis_os/environment/",
            "EnvironmentInteractionService",
            "GenericSimulationAdapter",
            "PolicyEvaluator",
            "ApprovalEvaluator",
            "InteractionReceipt",
            "LIVE",
            "No pipeline change"
        ) `
        -Label "Pre-existing Phase B specification"

    $spec = Replace-ExactlyOnce `
        -Text $spec `
        -OldValue "- **Status:** Proposed implementation specification" `
        -NewValue "- **Status:** Accepted implementation specification" `
        -Label "Phase B specification status"

    $spec = Replace-ExactlyOnce `
        -Text $spec `
        -OldValue "- **Decision record:** [ADR-006](../adr/ADR-006-environment-interaction-layer.md), Proposed" `
        -NewValue "- **Decision record:** [ADR-006](../adr/ADR-006-environment-interaction-layer.md), Accepted" `
        -Label "Phase B specification ADR status"

    $specAcceptance = @'

## WO-005 acceptance and governance boundary

- Acceptance date: 2026-07-31
- Governing work order: `WO-005`
- Architectural base: `be7502f73b51808d54728f912ead46ad0073c7b9`
- Governance amendment main: `ad743b4568bbd82527f7ff192c5b10ca4d59c2e9`
- Specification version: `1.0`
- Design disposition: accepted and implementation-ready
- Runtime disposition: not implemented and not authorized by this document

WO-005 reviewed this pre-existing proposed specification rather than replacing
it. Its provider-neutral contracts, exact package structure, deterministic
registry and resolver, separate policy and approval boundaries, simulated
adapter, normalized results, immutable receipts, failure taxonomy, validation
limits, security constraints, public exports, and test obligations form the
accepted contract for a later implementation work order.

The exact later runtime implementation boundary remains the package and focused
test structure already defined by this specification. That future work must
preserve simulation-only behavior, reject live mode before adapter invocation,
avoid current pipeline/execution integration, and introduce no external I/O,
credentials, persistence, observations, memory, learning, or autonomous action.

This accepted specification grants no authority to create Python modules,
modify tests, integrate or publish this candidate, push branches, modify
`main`, create tags or releases, alter rulesets, or clean up worktrees.
'@

    [System.IO.File]::WriteAllText(
        $specPath,
        $spec.TrimEnd() + $specAcceptance + "`n",
        $utf8NoBom
    )

    Write-Host "Pre-existing specification accepted through bounded revision: PASS"

    Write-Host "`n=== UPDATE ROADMAP STATE ==="

    $roadmap = [System.IO.File]::ReadAllText($roadmapPath)
    $roadmap = $roadmap -replace "`r`n", "`n"

    $oldRoadmapState = @'
Phase A is implemented. Phase B architecture is proposed; its runtime is not
implemented. See the current
[Environment Interaction Layer architecture](../architecture/environment-interaction-layer.md).
'@

    $newRoadmapState = @'
Phase A is implemented. Phase B architecture and implementation specification
are accepted; its runtime is not implemented. See the accepted
[Environment Interaction Layer architecture](../architecture/environment-interaction-layer.md)
and
[Phase B implementation specification](../specifications/v0.5-phase-b-environment-interaction-layer.md).
'@

    $roadmap = Replace-ExactlyOnce `
        -Text $roadmap `
        -OldValue $oldRoadmapState `
        -NewValue $newRoadmapState `
        -Label "roadmap Phase B state"

    $roadmap = Replace-ExactlyOnce `
        -Text $roadmap `
        -OldValue "and proposed`n  [ADR-006](../adr/ADR-006-environment-interaction-layer.md)" `
        -NewValue "and accepted`n  [ADR-006](../adr/ADR-006-environment-interaction-layer.md)" `
        -Label "roadmap ADR-006 state"

    [System.IO.File]::WriteAllText(
        $roadmapPath,
        $roadmap,
        $utf8NoBom
    )

    Write-Host "Roadmap accepted-design status: PASS"

    Write-Host "`n=== VALIDATE CANONICAL FOUR-DOCUMENT CANDIDATE ==="

    $changedPaths = @(
        git -C $candidateWorktree status --short |
            ForEach-Object { $_.Substring(3) }
    )

    Assert-ExactPathSet `
        -Actual $changedPaths `
        -Expected $deliverablePaths `
        -Label "WO-005 accepted candidate"

    Invoke-Native {
        git -C $candidateWorktree diff --check
    } "WO-005 candidate whitespace validation"

    $adrFinal = [System.IO.File]::ReadAllText($adrPath)
    $architectureFinal = [System.IO.File]::ReadAllText($architecturePath)
    $specFinal = [System.IO.File]::ReadAllText($specPath)
    $roadmapFinal = [System.IO.File]::ReadAllText($roadmapPath)

    Assert-ContainsAll `
        -Text $adrFinal `
        -Required @(
            "- **Status:** Accepted",
            "## WO-005 acceptance record",
            "Runtime implementation: not included"
        ) `
        -Label "Accepted ADR-006"

    Assert-ContainsAll `
        -Text $architectureFinal `
        -Required @(
            "Status: Accepted architecture; runtime not implemented.",
            "## WO-005 accepted-design handoff",
            "policy and approval precede adapter invocation"
        ) `
        -Label "Accepted architecture"

    Assert-ContainsAll `
        -Text $specFinal `
        -Required @(
            "- **Status:** Accepted implementation specification",
            "ADR-006](../adr/ADR-006-environment-interaction-layer.md), Accepted",
            "## WO-005 acceptance and governance boundary",
            "aegis_os/environment/service.py",
            "EnvironmentInteractionService",
            "GenericSimulationAdapter"
        ) `
        -Label "Accepted specification"

    Assert-ContainsAll `
        -Text $roadmapFinal `
        -Required @(
            "Phase B architecture and implementation specification",
            "are accepted; its runtime is not implemented",
            "Phase B implementation specification"
        ) `
        -Label "Updated roadmap"

    $forbiddenChanges = @(
        git -C $candidateWorktree diff `
            --name-only `
            $architecturalBase `
            -- `
            aegis_os `
            tests `
            pyproject.toml `
            .github `
            governance
    )

    if ($forbiddenChanges.Count -ne 0) {
        throw "The candidate contains forbidden code, test, dependency, CI, or governance changes."
    }

    Write-Host "Exact four-path boundary, accepted states, and zero executable delta: PASS"
    Write-Host "Git LF/CRLF conversion warnings: NON-BLOCKING"

    Write-Host "`n=== COMMIT CANONICAL CANDIDATE ==="

    Invoke-Native {
        git -C $candidateWorktree add -- $deliverablePaths
    } "WO-005 candidate staging"

    $stagedPaths = @(
        git -C $candidateWorktree diff --cached --name-only
    )

    Assert-ExactPathSet `
        -Actual $stagedPaths `
        -Expected $deliverablePaths `
        -Label "Staged WO-005 candidate"

    Invoke-Native {
        git -C $candidateWorktree diff --cached --check
    } "Staged WO-005 candidate validation"

    Invoke-Native {
        git -C $candidateWorktree commit -m $candidateSubject
    } "WO-005 candidate commit creation"

    $candidateCommit = (
        git -C $candidateWorktree rev-parse HEAD
    ).Trim()

    $candidateParent = (
        git -C $candidateWorktree rev-parse HEAD^
    ).Trim()

    $candidateTree = (
        git -C $candidateWorktree rev-parse "HEAD^{tree}"
    ).Trim()

    $candidateCommitSubject = (
        git -C $candidateWorktree log -1 --format=%s
    ).Trim()

    if ($candidateParent -ne $architecturalBase) {
        throw "WO-005 candidate parent mismatch."
    }

    if ($candidateCommitSubject -ne $candidateSubject) {
        throw "WO-005 candidate subject mismatch."
    }

    $committedDeliverablePaths = @(
        git -C $candidateWorktree diff-tree `
            --no-commit-id `
            --name-only `
            -r `
            HEAD
    )

    Assert-ExactPathSet `
        -Actual $committedDeliverablePaths `
        -Expected $deliverablePaths `
        -Label "Committed WO-005 candidate"

    if (@(git -C $candidateWorktree status --short).Count -ne 0) {
        throw "WO-005 candidate worktree is not clean after commit."
    }

    Write-Host "Canonical four-document candidate commit: CREATED"

    Write-Host "`n=== RECORD LOCAL CANDIDATE DESIGNATION ==="

    Invoke-Native {
        git -C $repo worktree add `
            -b $reviewBranch `
            $reviewWorktree `
            $governanceMain
    } "WO-005 candidate-review worktree creation"

    $workOrderPath = Join-Path $reviewWorktree $workOrderRelative
    $traceabilityPath = Join-Path $reviewWorktree $traceabilityRelative

    $workOrder = [System.IO.File]::ReadAllText($workOrderPath)
    $workOrder = $workOrder -replace "`r`n", "`n"

    if ($workOrder.Contains("## Candidate designation - accepted design")) {
        throw "WO-005 already contains an accepted-design candidate designation."
    }

    $workOrder = Replace-ExactlyOnce `
        -Text $workOrder `
        -OldValue "**Status:** ACTIVE - ARCHITECTURE AND PRE-EXISTING SPECIFICATION REVISION AUTHORIZED" `
        -NewValue "**Status:** ACTIVE - ACCEPTED-DESIGN CANDIDATE DESIGNATED FOR REVIEW" `
        -Label "WO-005 candidate-designation status"

    $oldDisposition = @'
WO-005: ACTIVE - ARCHITECTURE AND PRE-EXISTING SPECIFICATION REVISION AUTHORIZED
Authoritative base: be7502f73b51808d54728f912ead46ad0073c7b9
Specification at base: PRE-EXISTING - PROPOSED
Deliverable scope: FOUR EXISTING DOCUMENTATION PATHS
Deliverable candidate designated: NO
Architecture review: NOT STARTED
QA review: NOT STARTED
Deliverable integration authority: NOT GRANTED
Deliverable publication authority: NOT GRANTED
Runtime implementation authority: NOT GRANTED
'@

    $newDisposition = @"
WO-005: ACTIVE - ACCEPTED-DESIGN CANDIDATE DESIGNATED FOR REVIEW
Authoritative base: $architecturalBase
Governance amendment main: $governanceMain
Specification at base: PRE-EXISTING - PROPOSED
Deliverable scope: FOUR EXISTING DOCUMENTATION PATHS
Deliverable candidate designated: $candidateCommit
Candidate tree: $candidateTree
Architecture review: PENDING
QA review: PENDING
Deliverable integration authority: NOT GRANTED
Deliverable publication authority: NOT GRANTED
Runtime implementation authority: NOT GRANTED
"@

    $workOrder = Replace-ExactlyOnce `
        -Text $workOrder `
        -OldValue $oldDisposition `
        -NewValue $newDisposition.TrimEnd() `
        -Label "WO-005 current disposition"

    $designationSection = @"

## Candidate designation - accepted design

- Designation date: 2026-07-31
- Authoritative architectural base: ``$architecturalBase``
- Published governance amendment main: ``$governanceMain``
- Canonical candidate: ``$candidateCommit``
- Candidate parent: ``$candidateParent``
- Candidate tree: ``$candidateTree``
- Candidate subject: ``$candidateCommitSubject``
- Changed-path count: 4
- Pre-existing specification disposition: accepted through bounded revision
- Executable-code changes: 0
- Test changes: 0
- Dependency changes: 0
- CI changes: 0
- Governance changes in candidate: 0
- Candidate worktree clean: yes
- Architecture review: pending
- QA review: pending
- Integration authority: not granted
- Publication authority: not granted
- Runtime implementation authority: not granted

### Canonical candidate paths

1. ``$adrRelative``
2. ``$architectureRelative``
3. ``$specRelative``
4. ``$roadmapRelative``

### Review authority

Architecture Audit and QA & Verification are authorized to review only the
immutable candidate SHA and tree recorded above. Review must confirm
cross-document consistency, implementation-decision completeness,
deterministic and security boundaries, path preservation, and the absence of
runtime changes.

Any correction creates a new candidate and requires a new designation.
This record does not authorize integration, publication, push, modification of
``main``, runtime implementation, tags, releases, ruleset changes, or cleanup.
"@

    $workOrder = $workOrder.TrimEnd() + $designationSection + "`n"

    $traceability = [System.IO.File]::ReadAllText($traceabilityPath)
    $traceability = $traceability -replace "`r`n", "`n"

    if ($traceability.Contains("## TR-009 WO-005 Accepted-Design Candidate Designation")) {
        throw "TR-009 accepted-design candidate designation already exists."
    }

    $traceabilitySection = @"

## TR-009 WO-005 Accepted-Design Candidate Designation

- Work order: WO-005 - Environment Interaction Layer Architecture Acceptance and Implementation Specification
- Designation date: 2026-07-31
- Authoritative architectural base: ``$architecturalBase``
- Governance amendment main: ``$governanceMain``
- Canonical candidate: ``$candidateCommit``
- Candidate parent: ``$candidateParent``
- Candidate tree: ``$candidateTree``
- Candidate subject: ``$candidateCommitSubject``
- Candidate paths: exactly four existing documentation paths
- ADR-006 state in candidate: accepted
- Architecture state in candidate: accepted; runtime not implemented
- Specification state in candidate: accepted implementation specification
- Roadmap state in candidate: accepted design; runtime not implemented
- Executable, test, dependency, CI, and governance candidate changes: none
- Candidate state: **DESIGNATED FOR ARCHITECTURE AND QA REVIEW**
- Integration authority: not granted
- Publication authority: not granted
- Runtime implementation authority: not granted

Review must evaluate this immutable candidate. Any correction requires a new
candidate and designation. No remote reference, main branch, tag, release,
ruleset, runtime, or cleanup authority is granted.
"@

    $traceability = $traceability.TrimEnd() + $traceabilitySection + "`n"

    [System.IO.File]::WriteAllText(
        $workOrderPath,
        $workOrder,
        $utf8NoBom
    )

    [System.IO.File]::WriteAllText(
        $traceabilityPath,
        $traceability,
        $utf8NoBom
    )

    $reviewChangedPaths = @(
        git -C $reviewWorktree status --short |
            ForEach-Object { $_.Substring(3) }
    )

    Assert-ExactPathSet `
        -Actual $reviewChangedPaths `
        -Expected $governancePaths `
        -Label "WO-005 candidate designation"

    Invoke-Native {
        git -C $reviewWorktree diff --check
    } "WO-005 designation whitespace validation"

    Invoke-Native {
        git -C $reviewWorktree add -- $governancePaths
    } "WO-005 designation staging"

    $stagedGovernancePaths = @(
        git -C $reviewWorktree diff --cached --name-only
    )

    Assert-ExactPathSet `
        -Actual $stagedGovernancePaths `
        -Expected $governancePaths `
        -Label "Staged WO-005 candidate designation"

    Invoke-Native {
        git -C $reviewWorktree diff --cached --check
    } "Staged WO-005 designation validation"

    Invoke-Native {
        git -C $reviewWorktree commit -m $designationSubject
    } "WO-005 candidate-designation commit creation"

    $designationCommit = (
        git -C $reviewWorktree rev-parse HEAD
    ).Trim()

    $designationParent = (
        git -C $reviewWorktree rev-parse HEAD^
    ).Trim()

    $designationTree = (
        git -C $reviewWorktree rev-parse "HEAD^{tree}"
    ).Trim()

    if ($designationParent -ne $governanceMain) {
        throw "WO-005 designation parent mismatch."
    }

    $committedGovernancePaths = @(
        git -C $reviewWorktree diff-tree `
            --no-commit-id `
            --name-only `
            -r `
            HEAD
    )

    Assert-ExactPathSet `
        -Actual $committedGovernancePaths `
        -Expected $governancePaths `
        -Label "Committed WO-005 candidate designation"

    if (@(git -C $reviewWorktree status --short).Count -ne 0) {
        throw "WO-005 candidate-review worktree is not clean after commit."
    }

    Write-Host "Local governance candidate designation: CREATED"

    Write-Host "`n=== FINAL PRESERVATION AND MANIFEST ==="

    Invoke-Native {
        git -C $repo fetch origin `
            "+refs/heads/main:refs/remotes/origin/main"
    } "Final remote refresh"

    $finalLocalMain = (
        git -C $repo rev-parse refs/heads/main
    ).Trim()

    $finalOriginMain = (
        git -C $repo rev-parse refs/remotes/origin/main
    ).Trim()

    $finalLiveMain = Get-LiveRemoteMain $repo

    foreach ($identity in @(
        $finalLocalMain,
        $finalOriginMain,
        $finalLiveMain
    )) {
        if ($identity -ne $governanceMain) {
            throw "Main or remote changed during candidate creation and designation."
        }
    }

    Assert-AllWorktreesClean `
        -Repository $repo `
        -Label "Final"

    New-Item `
        -ItemType Directory `
        -Path $logDirectory `
        -Force | Out-Null

    $manifest = @"
AEGIS WO-005 Accepted Candidate Designation
===========================================

Date: 2026-07-31

Authoritative architectural base:
$architecturalBase

Published governance amendment main:
$governanceMain

Canonical technical candidate:
Commit: $candidateCommit
Parent: $candidateParent
Tree: $candidateTree
Subject: $candidateCommitSubject
Branch: $candidateBranch
Worktree: $candidateWorktree

Local governance designation:
Commit: $designationCommit
Parent: $designationParent
Tree: $designationTree
Subject: $designationSubject
Branch: $reviewBranch
Worktree: $reviewWorktree

Candidate paths:
$($committedDeliverablePaths -join "`r`n")

Governance designation paths:
$($committedGovernancePaths -join "`r`n")

Validation:
- Pre-existing specification revised, not recreated: PASS
- ADR-006 accepted: PASS
- Architecture accepted; runtime not implemented: PASS
- Specification accepted and implementation-ready: PASS
- Roadmap reconciled: PASS
- Exact candidate path count: 4
- Exact designation path count: 2
- Executable code changes: 0
- Test changes: 0
- Dependency changes: 0
- CI changes: 0
- Candidate governance changes: 0
- Worktrees clean: PASS
- Local main unchanged: PASS
- origin/main unchanged: PASS
- Live remote main unchanged: PASS
- Push performed: NO
- Integration authorized: NO
- Publication authorized: NO
- Runtime implementation authorized: NO
"@

    [System.IO.File]::WriteAllText(
        $manifestPath,
        $manifest,
        $utf8NoBom
    )

    Write-Host "`n=== WO-005 ACCEPTED CANDIDATE RESULT ==="

    [pscustomobject]@{
        ArchitecturalBase = $architecturalBase
        GovernanceMain = $governanceMain
        CandidateCommit = $candidateCommit
        CandidateParent = $candidateParent
        CandidateTree = $candidateTree
        CandidateSubject = $candidateCommitSubject
        CandidatePathCount = $committedDeliverablePaths.Count
        ADR006Status = "ACCEPTED"
        ArchitectureStatus = "ACCEPTED - RUNTIME NOT IMPLEMENTED"
        SpecificationStatus = "ACCEPTED IMPLEMENTATION SPECIFICATION"
        SpecificationTreatment = "PRE-EXISTING - BOUNDED REVISION"
        RoadmapStatus = "ACCEPTED DESIGN - RUNTIME NOT IMPLEMENTED"
        ExecutableCodeChanges = 0
        TestChanges = 0
        DependencyChanges = 0
        CIChanges = 0
        CandidateGovernanceChanges = 0
        DesignationCommit = $designationCommit
        DesignationParent = $designationParent
        DesignationTree = $designationTree
        DesignationPathCount = $committedGovernancePaths.Count
        LocalMain = $finalLocalMain
        OriginMain = $finalOriginMain
        LiveRemoteMain = $finalLiveMain
        RemoteMutation = "NONE"
        WorktreesClean = $true
        Manifest = $manifestPath
        ArchitectureReview = "PENDING"
        QAReview = "PENDING"
        IntegrationAuthorized = $false
        PublicationAuthorized = $false
        RuntimeImplementationAuthorized = $false
        FinalStatus = "WO-005 ACCEPTED-DESIGN CANDIDATE DESIGNATED FOR REVIEW"
    } | Format-List

    Write-Host "Canonical candidate paths:"
    $committedDeliverablePaths |
        ForEach-Object { Write-Host " - $_" }

    Write-Host "`nWO-005 ACCEPTED CANDIDATE: COMPLETE"
    Write-Host "The canonical four-document candidate is created and designated for Architecture and QA review."
    Write-Host "No push, main update, integration, runtime implementation, tag, release, ruleset change, or cleanup was performed."
}
catch {
    if (Test-Path -LiteralPath $candidateWorktree) {
        Write-Host "`nWO-005 candidate worktree preserved for diagnosis:"
        git -C $candidateWorktree status --short
    }

    if (Test-Path -LiteralPath $reviewWorktree) {
        Write-Host "`nWO-005 candidate-review worktree preserved for diagnosis:"
        git -C $reviewWorktree status --short
    }

    throw
}
