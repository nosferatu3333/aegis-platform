$ErrorActionPreference = "Stop"

if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$repo = "$env:USERPROFILE\Projects\aegis-platform"
$worktree = "$env:USERPROFILE\Projects\aegis-platform-wo-005-governance"
$branch = "governance/wo-005-environment-interaction-specification"

$expectedBase = "be7502f73b51808d54728f912ead46ad0073c7b9"
$commitSubject = "Authorize WO-005 environment interaction specification"

$workOrderRelative = "governance/work-orders/WO-005_ENVIRONMENT_INTERACTION_LAYER_SPECIFICATION.md"
$traceabilityRelative = "governance/TRACEABILITY.md"

$expectedPaths = @(
    $traceabilityRelative,
    $workOrderRelative
)

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

function Assert-ExactPathSet {
    param(
        [string[]]$Actual,
        [string[]]$Expected,
        [string]$Label
    )

    $unexpected = @($Actual | Where-Object { $_ -notin $Expected })
    $missing = @($Expected | Where-Object { $_ -notin $Actual })

    if (
        $Actual.Count -ne $Expected.Count -or
        $unexpected.Count -gt 0 -or
        $missing.Count -gt 0
    ) {
        Write-Host "$Label actual paths:"
        $Actual | ForEach-Object { Write-Host " - $_" }
        throw "$Label path boundary mismatch."
    }
}

function Get-RegisteredWorktrees {
    param([string]$Repository)

    $result = @()
    $currentPath = $null
    $currentBranch = $null

    foreach ($line in @(git -C $Repository worktree list --porcelain)) {
        if ($line -like "worktree *") {
            if ($currentPath) {
                $result += [pscustomobject]@{
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
            $result += [pscustomobject]@{
                Path = $currentPath
                Branch = $currentBranch
            }

            $currentPath = $null
            $currentBranch = $null
        }
    }

    if ($currentPath) {
        $result += [pscustomobject]@{
            Path = $currentPath
            Branch = $currentBranch
        }
    }

    return @($result)
}

function Assert-RegisteredWorktreesClean {
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

function Move-LocalMainFastForward {
    param(
        [string]$Repository,
        [string]$ExpectedOld,
        [string]$Target,
        [string]$Label
    )

    $currentMain = (git -C $Repository rev-parse refs/heads/main).Trim()

    if ($currentMain -eq $Target) {
        return
    }

    if ($currentMain -ne $ExpectedOld) {
        throw "$Label local main has an unexpected value: $currentMain"
    }

    Invoke-Native {
        git -C $Repository merge-base --is-ancestor $currentMain $Target
    } "$Label ancestry validation"

    $mainWorktree = @(
        Get-RegisteredWorktrees $Repository |
            Where-Object { $_.Branch -eq "refs/heads/main" }
    )

    if ($mainWorktree.Count -gt 1) {
        throw "$Label main is checked out in more than one worktree."
    }

    if ($mainWorktree.Count -eq 1) {
        if (@(git -C $mainWorktree[0].Path status --short).Count -ne 0) {
            throw "$Label main worktree is not clean."
        }

        Invoke-Native {
            git -C $mainWorktree[0].Path merge --ff-only $Target
        } "$Label checked-out main synchronization"
    }
    else {
        Invoke-Native {
            git -C $Repository branch -f main $Target
        } "$Label local main reference synchronization"
    }

    $updatedMain = (git -C $Repository rev-parse refs/heads/main).Trim()

    if ($updatedMain -ne $Target) {
        throw "$Label local main synchronization failed."
    }
}

Write-Host "`n=== WO-005 AUTHORIZATION PREFLIGHT ==="

if (-not (Test-Path -LiteralPath $repo)) {
    throw "Repository not found: $repo"
}

Invoke-Native {
    git -C $repo fetch origin `
        "+refs/heads/main:refs/remotes/origin/main"
} "Remote main refresh"

$originMain = (
    git -C $repo rev-parse refs/remotes/origin/main
).Trim()

$liveMain = Get-LiveRemoteMain $repo

if ($originMain -ne $expectedBase) {
    throw "origin/main does not match the authorized WO-005 base."
}

if ($liveMain -ne $expectedBase) {
    throw "Live remote main does not match the authorized WO-005 base."
}

Assert-RegisteredWorktreesClean `
    -Repository $repo `
    -Label "Preflight"

$localMainInitial = (
    git -C $repo rev-parse refs/heads/main
).Trim()

if ($localMainInitial -ne $expectedBase) {
    Invoke-Native {
        git -C $repo merge-base --is-ancestor `
            $localMainInitial `
            $expectedBase
    } "Local-main alignment ancestry"

    $mainWorktree = @(
        Get-RegisteredWorktrees $repo |
            Where-Object { $_.Branch -eq "refs/heads/main" }
    )

    if ($mainWorktree.Count -eq 1) {
        Invoke-Native {
            git -C $mainWorktree[0].Path merge --ff-only $expectedBase
        } "Initial checked-out main alignment"
    }
    elseif ($mainWorktree.Count -eq 0) {
        Invoke-Native {
            git -C $repo branch -f main $expectedBase
        } "Initial local main alignment"
    }
    else {
        throw "Main is checked out in more than one worktree."
    }
}

if ((git -C $repo rev-parse refs/heads/main).Trim() -ne $expectedBase) {
    throw "Local main could not be aligned with the authorized base."
}

if (Test-Path -LiteralPath $worktree) {
    throw "WO-005 governance worktree path already exists: $worktree"
}

if (@(git -C $repo branch --list $branch).Count -ne 0) {
    throw "WO-005 governance branch already exists: $branch"
}

$existingWorkOrderPath = @(
    git -C $repo ls-tree `
        -r `
        --name-only `
        $expectedBase `
        -- `
        $workOrderRelative
)

if ($LASTEXITCODE -ne 0) {
    throw "Unable to inspect the WO-005 work-order path on the authorized base."
}

if ($existingWorkOrderPath.Count -ne 0) {
    throw "The WO-005 work-order file already exists on the authorized base."
}

$traceabilityBase = @(
    git -C $repo show `
        "${expectedBase}:${traceabilityRelative}"
) -join "`n"

if ($LASTEXITCODE -ne 0) {
    throw "Unable to read the authoritative traceability file."
}

if ($traceabilityBase.Contains("## TR-007 WO-005")) {
    throw "A WO-005 TR-007 authorization record already exists."
}

Write-Host "Remote, local main, worktrees, and path identity: PASS"

Write-Host "`n=== CREATE WO-005 GOVERNANCE WORKTREE ==="

Invoke-Native {
    git -C $repo worktree add `
        -b $branch `
        $worktree `
        $expectedBase
} "WO-005 governance worktree creation"

$workOrderPath = Join-Path $worktree $workOrderRelative
$traceabilityPath = Join-Path $worktree $traceabilityRelative

try {
    Write-Host "`n=== WRITE WO-005 AUTHORIZATION RECORDS ==="

    $workOrderContent = @'
# Work Order WO-005: Environment Interaction Layer Architecture Acceptance and Implementation Specification

**Status:** ACTIVE - ARCHITECTURE AND SPECIFICATION WORK AUTHORIZED
**Authority:** Product Owner / Founder activation decision, recorded by Documentation & Governance
**Date authorized:** 2026-07-31
**Authoritative base:** `be7502f73b51808d54728f912ead46ad0073c7b9`
**Work owners:** Architecture; Documentation & Governance
**Required review owners:** Architecture Auditor; QA & Verification; Documentation & Governance
**Authorization-record publication:** GRANTED FOR THIS GOVERNANCE COMMIT ONLY
**Deliverable integration authority:** NOT GRANTED
**Deliverable remote-publication authority:** NOT GRANTED
**Governed by:** `governance/ENGINEERING_CHARTER.md`

---

## Objective

Convert the proposed v0.5 Phase B Environment Interaction Layer into an
accepted architectural decision and an implementation-ready specification,
without implementing the runtime.

WO-005 must settle the exact contracts, ownership boundaries, lifecycle,
determinism, security, failure behavior, module layout, future implementation
boundary, and validation obligations required before Phase B Python work may
begin.

## Authorization basis

The implemented Operational Resource Foundation can resolve semantic resource
requirements to stable `ResourceReference` values. The current platform still
has no provider-neutral environment-interaction runtime.

The current roadmap identifies v0.5 Phase B as the next planned platform
increment. The architecture document and ADR-006 are proposed and explicitly
require an implementation specification before runtime implementation.

WO-005 authorizes only the bounded documentation and specification work needed
to remove those open implementation decisions.

## Authoritative base

All WO-005 work must begin from exactly:

```text
be7502f73b51808d54728f912ead46ad0073c7b9
Close WO-004 after main publication
```

No earlier main state, preserved branch, unrelated worktree, rejected
candidate, or divergent governance lineage is authorized.

## Authorized deliverable paths

Only these architecture, decision, specification, and roadmap paths may differ
from the authoritative base in a WO-005 deliverable candidate:

1. `docs/adr/ADR-006-environment-interaction-layer.md`
2. `docs/architecture/environment-interaction-layer.md`
3. `docs/specifications/v0.5-phase-b-environment-interaction-layer.md` - new
4. `docs/roadmap/ROADMAP.md`

Any deliverable change outside this exact list requires a formal governance
amendment before the change is made.

## Governance record paths

Documentation & Governance may modify only these governance paths for WO-005
authorization and later disposition records:

1. `governance/TRACEABILITY.md`
2. `governance/work-orders/WO-005_ENVIRONMENT_INTERACTION_LAYER_SPECIFICATION.md`

These governance paths are not part of the deliverable candidate allowlist.

## Locked architectural direction

1. The layer is provider-neutral and simulation-first.
2. Resource resolution remains separate from environment resolution.
3. Cognition and capability selection must not invoke providers directly.
4. Requests, results, policy decisions, approval requirements, and receipts are
   explicit typed boundaries.
5. Environment and adapter registration is explicit and instance-owned.
6. Dynamic discovery, import-time registration, and adaptive ranking are
   excluded.
7. Environment selection is deterministic and precedes final policy
   evaluation.
8. Policy and approval are separate boundaries.
9. An adapter may declare support but may not authorize itself.
10. Simulation can never silently escalate to live execution.
11. Side effects and requested permissions are explicit.
12. The runtime is default-deny and least-privilege.
13. Results and failures are normalized and bounded.
14. Interaction receipts are immutable terminal audit evidence.
15. Provider objects, credentials, tokens, raw exceptions, and unbounded output
    do not cross the normalized boundary.
16. Current execution, API, dashboard, benchmark, and resource behavior remains
    unchanged under WO-005.
17. Runtime implementation requires a later, separately authorized work order.

## Specification decisions required

The WO-005 specification must define exact, implementation-ready decisions for:

- operation enum and semantic compatibility rules;
- environment identity and declaration contracts;
- adapter identity, declaration, support, and invocation protocol;
- immutable `EnvironmentRequest`;
- normalized `EnvironmentResult`;
- immutable `InteractionReceipt`;
- policy evaluator inputs, outcomes, evidence, and default behavior;
- approval requirement and approval evidence interfaces;
- explicit registry ownership and duplicate handling;
- deterministic resolution, stable ordering, and ambiguity behavior;
- resolved-resource reference validation and freshness handling;
- execution mode and simulation-only enforcement;
- permission and side-effect representation;
- idempotency and replay-sensitive request behavior;
- timeout and cancellation representation;
- partial-result shape and mapping;
- stable failure and reason-code taxonomy;
- safe bounded evidence and secret exclusion;
- correlation across request, resource resolution, interaction, workflow step,
  and execution identities;
- schema versioning and serialization;
- exact future Python module layout;
- exact future runtime implementation path allowlist;
- focused, regression, determinism, and security test requirements;
- benchmark implications without external-content grading.

Any unresolved item must be explicitly deferred with rationale and must not be
required to implement the first simulation-only runtime increment.

## Explicit exclusions

WO-005 does not authorize:

- Python or runtime implementation;
- modification of tests or benchmark fixtures;
- filesystem, network, HTTP, shell, process, Git, database, email, calendar,
  queue, browser, MCP, plugin, or external-agent integration;
- credentials, secrets, provider clients, or live adapters;
- real execution or external side effects;
- persistence, approval storage, task history, memory, learning, reflection, or
  observation generation;
- execution-pipeline integration;
- API, dashboard, or public-contract changes;
- dependency, packaging, CI, workflow, deployment, or infrastructure changes;
- repository cleanup;
- branch-protection or ruleset changes;
- tag or release creation;
- deliverable integration into `main`;
- deliverable push or remote publication;
- any path outside the exact authorized lists.

## Required deliverable content

The deliverable candidate must:

1. change ADR-006 from proposed to an explicitly reviewed decision state;
2. reconcile the architecture document with every locked decision;
3. create the complete Phase B implementation specification;
4. update the roadmap only as required to reflect the accepted design and the
   remaining runtime boundary;
5. identify the exact future implementation module and test paths;
6. define acceptance tests before implementation begins;
7. preserve all existing runtime and public behavior;
8. contain no executable implementation.

## Acceptance criteria

A WO-005 deliverable candidate is eligible for review only when:

1. it descends from the exact authoritative base;
2. only the four authorized deliverable paths differ from the base;
3. ADR-006 and the architecture document agree;
4. the specification resolves every required implementation decision;
5. every intentionally deferred decision is explicit and non-blocking;
6. the future runtime allowlist is exact and bounded;
7. contract invariants and serialization requirements are testable;
8. deterministic registry and resolver behavior is fully specified;
9. policy and approval cannot be bypassed by adapters;
10. simulation-to-live escalation is structurally prohibited;
11. error, evidence, correlation, and receipt behavior is fully specified;
12. test and benchmark obligations are concrete;
13. no runtime, test, dependency, API, dashboard, or CI file changes;
14. `git diff --check` passes;
15. the candidate worktree is clean;
16. no unauthorized branch, tag, ruleset, main, or remote reference changes.

## Required validation evidence

The candidate review package must include:

- exact candidate SHA, tree, and parent;
- exact changed-path list;
- base-to-candidate ancestry;
- cross-document terminology and decision consistency;
- required-decision coverage;
- future implementation allowlist coverage;
- exclusions and deferred-decision coverage;
- internal-link validation;
- Markdown whitespace validation;
- confirmation of zero executable-code changes;
- clean-state verification;
- confirmation that `main`, tags, rulesets, and remote references remained
  unchanged during deliverable preparation and review.

## Review sequence

1. Architecture and Documentation create one bounded deliverable candidate.
2. Architecture Audit verifies ownership, lifecycle, security, determinism, and
   decision completeness.
3. QA & Verification verifies testability, failure coverage, path boundaries,
   consistency, and preservation.
4. Documentation & Governance reconciles all findings and records one verdict.
5. Any correction produces a new candidate and repeats review.
6. Deliverable integration requires separate explicit authorization.
7. Deliverable remote publication requires separate explicit authorization.
8. Runtime implementation requires a later separately authorized work order.

## Stop conditions

Work and review must stop if:

- the base identity differs;
- an unauthorized path changes;
- runtime code or tests are modified;
- the proposed layer can bypass policy or approval;
- simulation can silently become live;
- adapter or provider details leak into cognition contracts;
- required decisions remain implicit or contradictory;
- the candidate changes during review;
- evidence cannot be reproduced;
- `main`, a tag, a ruleset, or a remote reference changes without separate
  authority.

## Current disposition

```text
WO-005: ACTIVE - ARCHITECTURE AND SPECIFICATION WORK AUTHORIZED
Authoritative base: be7502f73b51808d54728f912ead46ad0073c7b9
Deliverable scope: FOUR DOCUMENTATION PATHS
Deliverable candidate designated: NO
Architecture review: NOT STARTED
QA review: NOT STARTED
Deliverable integration authority: NOT GRANTED
Deliverable publication authority: NOT GRANTED
Runtime implementation authority: NOT GRANTED
```
'@

    $traceability = [System.IO.File]::ReadAllText($traceabilityPath)
    $traceability = $traceability -replace "`r`n", "`n"

    if ($traceability.Contains("## TR-007 WO-005")) {
        throw "TR-007 WO-005 authorization already exists."
    }

    $traceabilitySection = @'

## TR-007 WO-005 Architecture and Specification Authorization

- Work order: WO-005 - Environment Interaction Layer Architecture Acceptance and Implementation Specification
- Authorization date: 2026-07-31
- Authoritative base: `be7502f73b51808d54728f912ead46ad0073c7b9`
- Status: **ACTIVE - ARCHITECTURE AND SPECIFICATION WORK AUTHORIZED**
- Work-order record: `governance/work-orders/WO-005_ENVIRONMENT_INTERACTION_LAYER_SPECIFICATION.md`
- Deliverable boundary: exactly four documentation paths
- Runtime implementation: not authorized
- Deliverable integration: not authorized
- Deliverable remote publication: not authorized
- Authorization-record publication: authorized for this governance commit only

The authorized work accepts no runtime implementation. It may reconcile
ADR-006, the Phase B architecture, the roadmap, and a new implementation
specification only within the exact documented boundary.

The future deliverable must define provider-neutral, deterministic,
simulation-first contracts and an exact later implementation allowlist before
any Phase B Python work may begin. Separate explicit authority is required for
candidate designation, integration, publication, and runtime implementation.
'@

    $workOrderDirectory = Split-Path -Parent $workOrderPath

    if (-not (Test-Path -LiteralPath $workOrderDirectory)) {
        New-Item `
            -ItemType Directory `
            -Path $workOrderDirectory `
            -Force | Out-Null
    }

    [System.IO.File]::WriteAllText(
        $workOrderPath,
        $workOrderContent.TrimEnd() + "`n",
        $utf8NoBom
    )

    [System.IO.File]::WriteAllText(
        $traceabilityPath,
        $traceability.TrimEnd() + $traceabilitySection + "`n",
        $utf8NoBom
    )

    Write-Host "WO-005 work order and TR-007 authorization: WRITTEN"

    Write-Host "`n=== VALIDATE WO-005 AUTHORIZATION ==="

    $changedPaths = @(
        git -C $worktree status --short |
            ForEach-Object { $_.Substring(3) }
    )

    Assert-ExactPathSet `
        -Actual $changedPaths `
        -Expected $expectedPaths `
        -Label "WO-005 authorization"

    Invoke-Native {
        git -C $worktree diff --check
    } "WO-005 authorization whitespace validation"

    $writtenWorkOrder = [System.IO.File]::ReadAllText($workOrderPath)
    $writtenTraceability = [System.IO.File]::ReadAllText($traceabilityPath)

    foreach ($requiredText in @(
        "ACTIVE - ARCHITECTURE AND SPECIFICATION WORK AUTHORIZED",
        "be7502f73b51808d54728f912ead46ad0073c7b9",
        "Runtime implementation authority: NOT GRANTED",
        "docs/specifications/v0.5-phase-b-environment-interaction-layer.md"
    )) {
        if (-not $writtenWorkOrder.Contains($requiredText)) {
            throw "Required work-order content is missing: $requiredText"
        }
    }

    if (-not $writtenTraceability.Contains(
        "## TR-007 WO-005 Architecture and Specification Authorization"
    )) {
        throw "Required TR-007 traceability section is missing."
    }

    Write-Host "Exact two-path governance boundary and content: PASS"

    Write-Host "`n=== COMMIT WO-005 AUTHORIZATION ==="

    Invoke-Native {
        git -C $worktree add -- $expectedPaths
    } "WO-005 authorization staging"

    $stagedPaths = @(
        git -C $worktree diff --cached --name-only
    )

    Assert-ExactPathSet `
        -Actual $stagedPaths `
        -Expected $expectedPaths `
        -Label "Staged WO-005 authorization"

    Invoke-Native {
        git -C $worktree diff --cached --check
    } "Staged WO-005 whitespace validation"

    Invoke-Native {
        git -C $worktree commit -m $commitSubject
    } "WO-005 authorization commit creation"

    $authorizationCommit = (
        git -C $worktree rev-parse HEAD
    ).Trim()

    $authorizationParent = (
        git -C $worktree rev-parse HEAD^
    ).Trim()

    $authorizationSubject = (
        git -C $worktree log -1 --format=%s
    ).Trim()

    $committedPaths = @(
        git -C $worktree diff-tree `
            --no-commit-id `
            --name-only `
            -r `
            HEAD
    )

    if ($authorizationParent -ne $expectedBase) {
        throw "WO-005 authorization commit parent mismatch."
    }

    if ($authorizationSubject -ne $commitSubject) {
        throw "WO-005 authorization commit subject mismatch."
    }

    Assert-ExactPathSet `
        -Actual $committedPaths `
        -Expected $expectedPaths `
        -Label "Committed WO-005 authorization"

    if (@(git -C $worktree status --short).Count -ne 0) {
        throw "WO-005 governance worktree is not clean after commit."
    }

    Write-Host "WO-005 governance-only authorization commit: CREATED"

    Write-Host "`n=== PRE-PUBLICATION IDENTITY ==="

    Invoke-Native {
        git -C $repo fetch origin `
            "+refs/heads/main:refs/remotes/origin/main"
    } "Pre-publication remote refresh"

    $remoteImmediatelyBefore = Get-LiveRemoteMain $repo
    $trackingImmediatelyBefore = (
        git -C $repo rev-parse refs/remotes/origin/main
    ).Trim()

    if ($remoteImmediatelyBefore -ne $expectedBase) {
        throw "Live remote main changed before WO-005 publication."
    }

    if ($trackingImmediatelyBefore -ne $expectedBase) {
        throw "origin/main changed before WO-005 publication."
    }

    Invoke-Native {
        git -C $worktree merge-base `
            --is-ancestor `
            $expectedBase `
            $authorizationCommit
    } "WO-005 fast-forward ancestry validation"

    Assert-RegisteredWorktreesClean `
        -Repository $repo `
        -Label "Pre-publication"

    Write-Host "Exact publication base and fast-forward ancestry: PASS"

    Write-Host "`n=== STRICT FAST-FORWARD WO-005 PUBLICATION ==="

    Invoke-Native {
        git -C $worktree push `
            --porcelain `
            origin `
            "${authorizationCommit}:refs/heads/main"
    } "WO-005 authorization fast-forward push"

    Write-Host "WO-005 authorization fast-forward push completed."

    Write-Host "`n=== VERIFY AND SYNCHRONIZE MAIN ==="

    Invoke-Native {
        git -C $repo fetch origin `
            "+refs/heads/main:refs/remotes/origin/main"
    } "Post-publication remote refresh"

    $remoteAfter = Get-LiveRemoteMain $repo
    $trackingAfter = (
        git -C $repo rev-parse refs/remotes/origin/main
    ).Trim()

    if ($remoteAfter -ne $authorizationCommit) {
        throw "Live remote main does not match the WO-005 authorization commit."
    }

    if ($trackingAfter -ne $authorizationCommit) {
        throw "origin/main does not match the WO-005 authorization commit."
    }

    Move-LocalMainFastForward `
        -Repository $repo `
        -ExpectedOld $expectedBase `
        -Target $authorizationCommit `
        -Label "WO-005 publication"

    $localMainAfter = (
        git -C $repo rev-parse refs/heads/main
    ).Trim()

    if ($localMainAfter -ne $authorizationCommit) {
        throw "Local main does not match the WO-005 authorization commit."
    }

    Write-Host "Remote, origin/main, and local main identity: PASS"

    Write-Host "`n=== FINAL PRESERVATION ==="

    Assert-RegisteredWorktreesClean `
        -Repository $repo `
        -Label "Final"

    $finalRemote = Get-LiveRemoteMain $repo
    $finalTracking = (
        git -C $repo rev-parse refs/remotes/origin/main
    ).Trim()

    $finalLocalMain = (
        git -C $repo rev-parse refs/heads/main
    ).Trim()

    $finalWorktreeHead = (
        git -C $worktree rev-parse HEAD
    ).Trim()

    foreach ($identity in @(
        $finalRemote,
        $finalTracking,
        $finalLocalMain,
        $finalWorktreeHead
    )) {
        if ($identity -ne $authorizationCommit) {
            throw "Final WO-005 authorization identities do not match."
        }
    }

    Write-Host "`n=== WO-005 AUTHORIZATION RESULT ==="

    [pscustomobject]@{
        AuthoritativeBase = $expectedBase
        AuthorizationCommit = $authorizationCommit
        AuthorizationParent = $authorizationParent
        AuthorizationSubject = $authorizationSubject
        AuthorizationPathCount = $committedPaths.Count
        LiveRemoteMain = $finalRemote
        OriginMain = $finalTracking
        LocalMain = $finalLocalMain
        GovernanceWorktreeHead = $finalWorktreeHead
        DeliverablePathCount = 4
        RuntimeImplementationAuthorized = $false
        DeliverableIntegrationAuthorized = $false
        DeliverablePublicationAuthorized = $false
        PushType = "STRICT FAST-FORWARD"
        ForcePush = $false
        MergeCommit = $false
        TagCreated = $false
        ReleaseCreated = $false
        WorktreesClean = $true
        FinalStatus = "WO-005 AUTHORIZED"
    } | Format-List

    Write-Host "Authorization paths:"
    $committedPaths | ForEach-Object { Write-Host " - $_" }

    Write-Host "`nWO-005 GOVERNANCE AUTHORIZATION: COMPLETE"
    Write-Host "Architecture and specification work is authorized."
    Write-Host "Runtime implementation, deliverable integration, and deliverable publication remain unauthorized."
}
catch {
    if (Test-Path -LiteralPath $worktree) {
        Write-Host "`nWO-005 governance worktree preserved for diagnosis:"
        git -C $worktree status --short
    }

    throw
}
