$ErrorActionPreference = "Stop"
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$repo = "$env:USERPROFILE\Projects\aegis-platform"
$mainWorktree = "$env:USERPROFILE\Projects\aegis-platform-wo-005-local-integration"
$enablingWorktree = "$env:USERPROFILE\Projects\aegis-platform-wo-006-enabling"
$enablingBranch = "governance/wo-006-enabling"
$baseMain = "cfae92111eeb5355873a8c32c649514853564743"

$archiveSubject = "Archive operational scripts before WO-006 enabling"
$enablingSubject = "Record WO-006 enabling boundary"

$sourceOperations = Join-Path $repo "tools\operations"
$specRelative = "docs/specifications/v0.5-phase-b-environment-interaction-layer.md"
$traceabilityRelative = "governance/TRACEABILITY.md"
$workOrderRelative = "governance/work-orders/WO-006_ENVIRONMENT_INTERACTION_LAYER_SIMULATION_RUNTIME.md"
$governancePaths = @($specRelative, $traceabilityRelative, $workOrderRelative)

$runtimePaths = @(
    "aegis_os/environment/__init__.py",
    "aegis_os/environment/models.py",
    "aegis_os/environment/errors.py",
    "aegis_os/environment/adapter.py",
    "aegis_os/environment/registry.py",
    "aegis_os/environment/resolver.py",
    "aegis_os/environment/policy.py",
    "aegis_os/environment/approvals.py",
    "aegis_os/environment/service.py",
    "aegis_os/environment/simulated.py"
)

$testPaths = @(
    "tests/environment/__init__.py",
    "tests/environment/conftest.py",
    "tests/environment/test_models.py",
    "tests/environment/test_registry.py",
    "tests/environment/test_resolver.py",
    "tests/environment/test_policy.py",
    "tests/environment/test_approvals.py",
    "tests/environment/test_adapter.py",
    "tests/environment/test_simulated.py",
    "tests/environment/test_service.py",
    "tests/environment/test_receipts.py",
    "tests/environment/test_determinism.py"
)

$operationsRoot = [Environment]::GetEnvironmentVariable("AEGIS_OPERATIONS", "User")
if ([string]::IsNullOrWhiteSpace($operationsRoot)) {
    $operationsRoot = "$env:USERPROFILE\Projects\AEGIS-operations"
}
$logDirectory = Join-Path $operationsRoot "logs\WO-006"
$manifestPath = Join-Path $logDirectory "WO-006-enabling-local-commits.txt"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Invoke-Native {
    param([scriptblock]$Command, [string]$Label, [switch]$AllowFailure)
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = @(& $Command)
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $saved
    }
    if (-not $AllowFailure -and $exitCode -ne 0) {
        throw "$Label failed with exit code $exitCode."
    }
    [pscustomobject]@{ Output = $output; ExitCode = $exitCode }
}

function Get-LiveMain {
    param([string]$Repository)
    $result = Invoke-Native { git -C $Repository ls-remote --heads origin refs/heads/main } "Live remote main lookup"
    if ($result.Output.Count -ne 1) { throw "Expected exactly one live remote main ref." }
    (($result.Output[0] -split "\s+")[0]).Trim()
}

function Get-RemoteSnapshot {
    param([string]$Repository)
    $result = Invoke-Native { git -C $Repository ls-remote --heads --tags origin } "Remote snapshot"
    @($result.Output | ForEach-Object { $_.Trim() } | Where-Object { $_ } | Sort-Object)
}

function Assert-SameSequence {
    param([string[]]$Before, [string[]]$After, [string]$Label)
    if ($Before.Count -ne $After.Count) { throw "$Label count changed." }
    for ($i = 0; $i -lt $Before.Count; $i++) {
        if ($Before[$i] -ne $After[$i]) { throw "$Label changed." }
    }
}

function Get-WorktreePaths {
    param([string]$Repository)
    @(
        git -C $Repository worktree list --porcelain |
        Where-Object { $_ -like "worktree *" } |
        ForEach-Object { $_.Substring(9) }
    )
}

function Assert-SourceBoundary {
    param([string]$Repository)
    $status = @(git -C $Repository status --short)
    if ($status.Count -eq 0) { throw "No untracked tools archive exists in the source worktree." }
    $unexpected = @($status | Where-Object { $_ -notmatch '^\?\? tools[/\\]' })
    if ($unexpected.Count -gt 0) {
        $unexpected | ForEach-Object { Write-Host "Unexpected: $_" }
        throw "Source worktree contains changes outside untracked tools/."
    }
}

function Normalize-WorktreePath {
    param([string]$Path)

    return ([System.IO.Path]::GetFullPath($Path)).
        Replace([char]92, [char]47).
        TrimEnd([char]47).
        ToLowerInvariant()
}

function Assert-OtherWorktreesClean {
    param(
        [string]$Repository,
        [string[]]$AllowedDirty
    )

    $allowed = @(
        $AllowedDirty |
            ForEach-Object { Normalize-WorktreePath $_ }
    )

    foreach ($path in @(Get-WorktreePaths $Repository)) {
        $normalized = Normalize-WorktreePath $path

        if ($normalized -in $allowed) {
            continue
        }

        if (@(git -C $path status --short).Count -ne 0) {
            throw "Unexpected dirty worktree: $path"
        }
    }
}

function Assert-ExactPaths {
    param([string[]]$Actual, [string[]]$Expected, [string]$Label)
    $a = @($Actual | Sort-Object -Unique)
    $e = @($Expected | Sort-Object -Unique)
    if ($a.Count -ne $e.Count) {
        Write-Host "$Label paths:"; $a | ForEach-Object { Write-Host " - $_" }
        throw "$Label path count mismatch."
    }
    foreach ($path in $e) {
        if ($path -notin $a) { throw "$Label is missing $path" }
    }
}

function Replace-Once {
    param([string]$Text, [string]$Old, [string]$New, [string]$Label)
    $first = $Text.IndexOf($Old, [System.StringComparison]::Ordinal)
    if ($first -lt 0) { throw "Required text not found: $Label" }
    $second = $Text.IndexOf($Old, $first + $Old.Length, [System.StringComparison]::Ordinal)
    if ($second -ge 0) { throw "Required text occurs more than once: $Label" }
    $Text.Substring(0, $first) + $New + $Text.Substring($first + $Old.Length)
}

function Normalize-WO006Archive {
    param([string]$OperationsDirectory)
    $wo006 = Join-Path $OperationsDirectory "WO-006"
    $scripts = Join-Path $wo006 "scripts"
    $target = Join-Path $scripts "wo006_enabling_preflight.ps1"
    New-Item -ItemType Directory -Path $scripts -Force | Out-Null

    $candidates = @(
        Get-ChildItem -LiteralPath $wo006 -Recurse -File -Filter "wo006_enabling_preflight*.ps1" -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -ne $target } |
        Sort-Object LastWriteTime -Descending
    )

    if (-not (Test-Path -LiteralPath $target)) {
        if ($candidates.Count -eq 0) { throw "WO-006 preflight script was not found in tools/operations/WO-006." }
        Move-Item -LiteralPath $candidates[0].FullName -Destination $target -Force
        $candidates = @($candidates | Select-Object -Skip 1)
    }

    $targetHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
    foreach ($candidate in $candidates) {
        $candidateHash = (Get-FileHash -LiteralPath $candidate.FullName -Algorithm SHA256).Hash
        if ($candidateHash -eq $targetHash) {
            Remove-Item -LiteralPath $candidate.FullName -Force
        }
        else {
            $short = $candidateHash.Substring(0,10).ToLowerInvariant()
            Move-Item -LiteralPath $candidate.FullName -Destination (Join-Path $scripts "wo006_enabling_preflight__$short.ps1") -Force
        }
    }

    if ($PSCommandPath) {
        Copy-Item -LiteralPath $PSCommandPath -Destination (Join-Path $scripts "prepare_wo006_enabling_commits.ps1") -Force
    }

    $hashLines = @(
        Get-ChildItem -LiteralPath $scripts -File -Filter "*.ps1" |
        Sort-Object Name |
        ForEach-Object {
            $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            "$hash  $($_.Name)"
        }
    )
    [System.IO.File]::WriteAllLines((Join-Path $wo006 "SHA256SUMS.txt"), $hashLines, $utf8NoBom)
}

Write-Host "`n=== WO-006 TWO-COMMIT PREFLIGHT ==="

if (-not (Test-Path -LiteralPath $repo)) { throw "Repository not found: $repo" }
if (-not (Test-Path -LiteralPath $mainWorktree)) { throw "Main worktree not found: $mainWorktree" }
if (-not (Test-Path -LiteralPath $sourceOperations)) { throw "Operations archive not found: $sourceOperations" }

Invoke-Native { git -C $repo fetch origin "+refs/heads/main:refs/remotes/origin/main" } "Fetch main" | Out-Null
$localMainBefore = (git -C $repo rev-parse refs/heads/main).Trim()
$originMainBefore = (git -C $repo rev-parse refs/remotes/origin/main).Trim()
$liveMainBefore = Get-LiveMain $repo
foreach ($identity in @($localMainBefore, $originMainBefore, $liveMainBefore)) {
    if ($identity -ne $baseMain) { throw "Main identity differs from the WO-005 closure base." }
}
if ((git -C $mainWorktree rev-parse HEAD).Trim() -ne $baseMain) { throw "Checked-out main worktree is not at the closure base." }
if (@(git -C $mainWorktree status --short).Count -ne 0) { throw "Checked-out main worktree is dirty." }

Assert-SourceBoundary $repo
Assert-OtherWorktreesClean -Repository $repo -AllowedDirty @($repo, $enablingWorktree)

$reuseEnablingWorktree = $false

if (Test-Path -LiteralPath $enablingWorktree) {
    $existingBranch = (
        git -C $enablingWorktree branch --show-current
    ).Trim()

    $existingHead = (
        git -C $enablingWorktree rev-parse HEAD
    ).Trim()

    if ($existingBranch -ne $enablingBranch) {
        throw "Existing enabling worktree has unexpected branch: $existingBranch"
    }

    if ($existingHead -ne $baseMain) {
        throw "Existing enabling worktree has unexpected HEAD: $existingHead"
    }

    $existingPaths = @(
        git -C $enablingWorktree ls-files --others --exclude-standard
        git -C $enablingWorktree diff --name-only
        git -C $enablingWorktree diff --cached --name-only
    ) | Sort-Object -Unique

    $unexpectedExistingPaths = @(
        $existingPaths |
            Where-Object { $_ -notlike 'tools/operations/*' }
    )

    if ($unexpectedExistingPaths.Count -gt 0) {
        Write-Host "Unexpected existing paths:"
        $unexpectedExistingPaths |
            ForEach-Object { Write-Host " - $_" }

        throw "Existing enabling worktree contains changes outside tools/operations."
    }

    $reuseEnablingWorktree = $true
}
elseif (@(git -C $repo branch --list $enablingBranch).Count -ne 0) {
    throw "Enabling branch exists without its expected worktree."
}

$remoteBefore = Get-RemoteSnapshot $repo
Write-Host "Base identities and preservation gates: PASS"

if (-not $reuseEnablingWorktree) {
    Invoke-Native {
        git -C $repo worktree add -b $enablingBranch $enablingWorktree $baseMain
    } "Create enabling worktree" | Out-Null
}
else {
    Write-Host "Reusing preserved WO-006 enabling worktree."
}

try {
    Write-Host "`n=== COMMIT 1: OPERATIONS ARCHIVE ==="
    $destinationOperations = Join-Path $enablingWorktree "tools\operations"
    New-Item -ItemType Directory -Path $destinationOperations -Force | Out-Null
    Get-ChildItem -LiteralPath $sourceOperations -Force | Copy-Item -Destination $destinationOperations -Recurse -Force
    Normalize-WO006Archive $destinationOperations

    $archiveStatusPaths = @(
        git -C $enablingWorktree ls-files --others --exclude-standard
        git -C $enablingWorktree diff --name-only
        git -C $enablingWorktree diff --cached --name-only
    ) | Sort-Object -Unique
    if ($archiveStatusPaths.Count -eq 0) { throw "No archive files were copied." }
    if (@($archiveStatusPaths | Where-Object { $_ -notlike 'tools/operations/*' }).Count -gt 0) {
        throw "Archive preparation escaped tools/operations/."
    }

    Invoke-Native { git -C $enablingWorktree add -- tools/operations } "Stage archive" | Out-Null
    $archiveValidation = Invoke-Native {
    git -C $enablingWorktree diff --cached --check
} "Validate archive" -AllowFailure

if ($archiveValidation.ExitCode -ne 0) {
    Write-Host "Historical archive whitespace findings preserved as non-blocking evidence:"
    $archiveValidation.Output | ForEach-Object {
        Write-Host " - $_"
    }
}
    $archiveStaged = @(git -C $enablingWorktree diff --cached --name-only)
    if ($archiveStaged.Count -eq 0) { throw "No archive paths staged." }
    if (@($archiveStaged | Where-Object { $_ -notlike 'tools/operations/*' }).Count -gt 0) {
        throw "Staged archive escaped tools/operations/."
    }

    Invoke-Native { git -C $enablingWorktree commit -m $archiveSubject } "Create archive commit" | Out-Null
    $archiveCommit = (git -C $enablingWorktree rev-parse HEAD).Trim()
    $archiveParent = (git -C $enablingWorktree rev-parse HEAD^).Trim()
    $archiveTree = (git -C $enablingWorktree rev-parse "HEAD^{tree}").Trim()
    if ($archiveParent -ne $baseMain) { throw "Archive parent mismatch." }
    if ((git -C $enablingWorktree log -1 --format=%s).Trim() -ne $archiveSubject) { throw "Archive subject mismatch." }
    $archiveCommitted = @(git -C $enablingWorktree diff-tree --no-commit-id --name-only -r $archiveCommit)
    if (@($archiveCommitted | Where-Object { $_ -notlike 'tools/operations/*' }).Count -gt 0) {
        throw "Archive commit escaped tools/operations/."
    }
    Write-Host "Archive commit:" $archiveCommit

    Write-Host "`n=== COMMIT 2: WO-006 ENABLING BOUNDARY ==="
    $specPath = Join-Path $enablingWorktree $specRelative
    $traceabilityPath = Join-Path $enablingWorktree $traceabilityRelative
    $workOrderPath = Join-Path $enablingWorktree $workOrderRelative

    $spec = [System.IO.File]::ReadAllText($specPath) -replace "`r`n", "`n"
    $trace = [System.IO.File]::ReadAllText($traceabilityPath) -replace "`r`n", "`n"
    if ($spec.Contains("## WO-006 enabling correction")) { throw "WO-006 correction already exists." }
    if ($trace.Contains("## TR-014 WO-006 Enabling Boundary")) { throw "TR-014 already exists." }
    if (Test-Path -LiteralPath $workOrderPath) { throw "WO-006 work order already exists." }

    $spec = Replace-Once $spec "14. ADR-006 review." "14. ADR-006 accepted-state verification." "section 45"

    $old47 = @"
## 47. ADR-006 acceptance conditions

ADR-006 may move from Proposed to Accepted only after this specification is
committed, the exact simulation runtime is implemented, all required tests and
benchmarks pass, external I/O/global state are absent, determinism and security
invariants are proven, provider neutrality and architecture alignment are
reviewed, and current pipeline behavior remains unchanged.

This task MUST NOT change ADR-006 status.
"@

    $new47 = @"
## 47. ADR-006 accepted-state preservation

ADR-006 is already Accepted through the completed WO-005 architecture review,
publication, and closure. Phase B runtime acceptance SHALL verify that the
implementation conforms to the accepted ADR, this specification, required
tests, separately authorized benchmark evidence, external-I/O and global-state
prohibitions, determinism and security invariants, provider neutrality,
architecture alignment, and preservation of current pipeline behavior.

The implementation task MUST NOT change ADR-006 status. Any future amendment,
supersession, or reversal requires a separate architecture-governance decision.
"@

    $spec = Replace-Once $spec $old47.TrimEnd() $new47.TrimEnd() "section 47"
    $spec = Replace-Once $spec `
        "| ADR-006 | Remains Proposed until runtime acceptance evidence | Accepted after verification |" `
        "| ADR-006 | Remains Accepted during runtime implementation and verification | Amendment or supersession requires separate architecture governance |" `
        "section 49"

    $specAppend = @"

## WO-006 enabling correction

- Correction date: 2026-08-01
- Enabling base: $baseMain
- Governing preparation: WO-006
- Correction scope: stale ADR-006 status language in sections 45, 47, and 49
- ADR-006 status before correction: Accepted
- ADR-006 status after correction: Accepted
- Runtime implementation authority granted by this correction: no
- Benchmark implementation authority granted by this correction: no
- Integration or publication authority granted by this correction: no

WO-005 accepted and published ADR-006 before runtime implementation. Sections
45, 47, and 49 retained older pre-acceptance wording that incorrectly described
ADR-006 as Proposed or scheduled a later status transition. This bounded
correction reconciles those sections with the authoritative Accepted state
without changing the architecture, implementation contract, package surface,
runtime behavior, test obligations, or security boundaries.

The accepted-state verification remains a required runtime acceptance gate.
This correction does not authorize creation of the Phase B package, tests,
benchmarks, integrations, providers, external I/O, tags, releases, ruleset
changes, main modification, remote publication, or worktree cleanup.
"@
    $spec = $spec.TrimEnd() + $specAppend + "`n"

    $runtimeList = ($runtimePaths | ForEach-Object { "- $_" }) -join "`n"
    $testList = ($testPaths | ForEach-Object { "- $_" }) -join "`n"

    $workOrder = @"
# Work Order WO-006: Environment Interaction Layer Simulation Runtime

**Status:** ENABLING - LOCAL GOVERNANCE CANDIDATE; ACTIVATION NOT GRANTED
**Preparation authorized:** 2026-08-01
**Authoritative base:** $baseMain
**Architecture authority:** docs/adr/ADR-006-environment-interaction-layer.md
**Implementation authority:** $specRelative
**Runtime implementation authority:** NOT GRANTED
**Benchmark implementation authority:** NOT GRANTED
**Integration authority:** NOT GRANTED
**Remote-publication authority:** NOT GRANTED
**Tag and release authority:** NOT GRANTED
**Ruleset-change authority:** NOT GRANTED
**Worktree-cleanup authority:** NOT GRANTED

---

## Objective

Prepare the exact governance boundary for a later, separately activated
implementation of the deterministic, provider-neutral, simulation-only Phase B
Environment Interaction Layer.

This enabling record resolves stale ADR-006 status wording and identifies the
only runtime and focused-test paths that may become eligible under a later
explicit activation. It does not authorize Python implementation.

## Enabling base

All WO-006 preparation descends from exactly $baseMain, the commit titled
Close WO-005 after main publication.

At that base, WO-005 is closed, ADR-006 and the Phase B specification are
Accepted, the Phase B runtime is absent, and runtime implementation remains
unauthorized.

## Current enabling paths

This local enabling candidate may change only:

1. $specRelative
2. $traceabilityRelative
3. $workOrderRelative

## Future runtime implementation allowlist

A later explicit WO-006 activation may authorize exactly:

$runtimeList

No other aegis_os path is eligible under this enabling record.

## Future focused-test allowlist

A later explicit WO-006 activation may authorize exactly:

$testList

No existing test path may be modified merely because this work order exists.

## Benchmark boundary

The accepted specification requires a separate simulation-only Phase B
benchmark corpus and states that benchmark-harness changes require a separate
implementation task. This enabling record grants no benchmark-file authority.
A separate decision must identify exact benchmark paths and validation gates
without modifying the existing 17 missions.

## Locked implementation direction

Any later activation must preserve simulation-only operation, deterministic
instance-owned composition, exact Phase A resource lookup without
re-resolution, provider neutrality, default-deny policy, separate approval,
one GenericSimulationAdapter, immutable bounded results and receipts, no
current pipeline or execution-engine integration, no persistence or autonomous
behavior, no dependency drift, and no filesystem, network, process, shell,
provider, credential, clock, randomness, environment, or machine-state access.

## Activation prerequisites

Runtime implementation may begin only after a separate explicit authorization
records the exact enabling-candidate SHA and tree, independent review, exact
runtime and test boundaries, implementation worktree, validation commands,
preservation gates, and the separate benchmark decision.

## Stop conditions

Stop before implementation if the base or accepted design differs, an internal
contradiction remains, a path falls outside the future allowlists, live or
external-I/O behavior is proposed, current execution integration is proposed,
benchmark paths lack separate authority, unrelated worktree changes exist, or
main or a remote reference changes without separate authority.

## Current disposition

WO-006: ENABLING - LOCAL GOVERNANCE CANDIDATE
Authoritative base: $baseMain
ADR-006 state: ACCEPTED - PRESERVED
Specification contradiction: CORRECTED IN LOCAL CANDIDATE
Operations archive: COMMITTED IN PARENT LOCAL COMMIT
Runtime implementation authority: NOT GRANTED
Benchmark implementation authority: NOT GRANTED
Integration authority: NOT GRANTED
Remote publication authority: NOT GRANTED
Tag or release authority: NOT GRANTED
Ruleset-change authority: NOT GRANTED
Worktree-cleanup authority: NOT GRANTED
Next required action: INDEPENDENT REVIEW AND SEPARATE ACTIVATION DECISION
"@

    New-Item -ItemType Directory -Path (Split-Path -Parent $workOrderPath) -Force | Out-Null
    [System.IO.File]::WriteAllText($workOrderPath, $workOrder.TrimEnd() + "`n", $utf8NoBom)

    $traceAppend = @"

## TR-014 WO-006 Enabling Boundary

- Record date: 2026-08-01
- Work order: WO-006 - Environment Interaction Layer Simulation Runtime
- Authoritative base: $baseMain
- Parent local operations-archive commit: $archiveCommit
- ADR-006 authoritative state: ACCEPTED
- Contradiction found: sections 45, 47, and 49 retained stale pre-acceptance language
- Correction result: Accepted ADR state preserved; stale Proposed-transition language removed
- Runtime package allowlist: 10 future paths
- Focused-test allowlist: 12 future paths
- Benchmark path authority: not granted; separate exact-path task required
- Runtime implementation authority: not granted
- Integration authority: not granted
- Remote-publication authority: not granted
- Tag, release, and ruleset authority: not granted
- Worktree cleanup: not authorized
- Current disposition: LOCAL ENABLING CANDIDATE - REVIEW REQUIRED

The local enabling candidate reconciles the already Accepted ADR-006 state with
the accepted Phase B specification and creates the bounded WO-006 preparation
record. It does not create or modify runtime, tests, benchmarks, dependencies,
CI, API, dashboard, execution, providers, or external integrations.

A later activation requires independent review and separate explicit Product
Owner / Founder authorization.
"@
    $trace = $trace.TrimEnd() + $traceAppend + "`n"

    [System.IO.File]::WriteAllText($specPath, $spec, $utf8NoBom)
    [System.IO.File]::WriteAllText($traceabilityPath, $trace, $utf8NoBom)

    $changed = @(git -C $enablingWorktree status --short | ForEach-Object { $_.Substring(3) })
    Assert-ExactPaths $changed $governancePaths "WO-006 enabling candidate"
    Invoke-Native { git -C $enablingWorktree diff --check } "Validate enabling diff" | Out-Null

    $forbidden = @(git -C $enablingWorktree diff --name-only $archiveCommit -- aegis_os tests benchmarks pyproject.toml .github)
    if ($forbidden.Count -ne 0) { throw "Enabling candidate changed technical paths." }

    Invoke-Native { git -C $enablingWorktree add -- $governancePaths } "Stage enabling candidate" | Out-Null
    $staged = @(git -C $enablingWorktree diff --cached --name-only)
    Assert-ExactPaths $staged $governancePaths "Staged enabling candidate"
    Invoke-Native { git -C $enablingWorktree diff --cached --check } "Validate staged enabling candidate" | Out-Null
    Invoke-Native { git -C $enablingWorktree commit -m $enablingSubject } "Create enabling commit" | Out-Null

    $enablingCommit = (git -C $enablingWorktree rev-parse HEAD).Trim()
    $enablingParent = (git -C $enablingWorktree rev-parse HEAD^).Trim()
    $enablingTree = (git -C $enablingWorktree rev-parse "HEAD^{tree}").Trim()
    if ($enablingParent -ne $archiveCommit) { throw "Enabling parent mismatch." }
    if ((git -C $enablingWorktree log -1 --format=%s).Trim() -ne $enablingSubject) { throw "Enabling subject mismatch." }
    $enablingCommitted = @(git -C $enablingWorktree diff-tree --no-commit-id --name-only -r $enablingCommit)
    Assert-ExactPaths $enablingCommitted $governancePaths "Committed enabling candidate"
    if (@(git -C $enablingWorktree status --short).Count -ne 0) { throw "Enabling worktree is dirty after commit." }

    Write-Host "Enabling commit:" $enablingCommit
    Write-Host "`n=== VERIFY LOCAL LINEAGE AND PRESERVATION ==="

    $commitCount = [int](git -C $enablingWorktree rev-list --count "$baseMain..$enablingCommit").Trim()
    if ($commitCount -ne 2) { throw "Expected exactly two local commits." }
    $mergeCount = @(git -C $enablingWorktree rev-list --merges "$baseMain..$enablingCommit").Count
    if ($mergeCount -ne 0) { throw "Local lineage contains a merge commit." }

    $technical = @(git -C $enablingWorktree diff --name-only $baseMain $enablingCommit -- aegis_os tests benchmarks pyproject.toml .github)
    if ($technical.Count -ne 0) { throw "Two-commit lineage contains technical changes." }

    $localMainAfter = (git -C $repo rev-parse refs/heads/main).Trim()
    $originMainAfter = (git -C $repo rev-parse refs/remotes/origin/main).Trim()
    $liveMainAfter = Get-LiveMain $repo
    foreach ($identity in @($localMainAfter, $originMainAfter, $liveMainAfter)) {
        if ($identity -ne $baseMain) { throw "Main changed during local preparation." }
    }

    Assert-SameSequence $remoteBefore (Get-RemoteSnapshot $repo) "Remote refs"
    Assert-SourceBoundary $repo
    Assert-OtherWorktreesClean -Repository $repo -AllowedDirty $repo

    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
    $manifest = @"
AEGIS WO-006 Enabling Local Commits
===================================
Date: 2026-08-01
Base: $baseMain
Archive commit: $archiveCommit
Archive parent: $archiveParent
Archive tree: $archiveTree
Archive subject: $archiveSubject
Archive path count: $($archiveCommitted.Count)
Enabling commit: $enablingCommit
Enabling parent: $enablingParent
Enabling tree: $enablingTree
Enabling subject: $enablingSubject
Enabling paths:
$($enablingCommitted -join "`r`n")
Validation:
- Local commit count: 2
- Merge commits: 0
- Runtime changes: 0
- Test changes: 0
- Benchmark changes: 0
- Dependency changes: 0
- CI changes: 0
- Main changed: NO
- Push performed: NO
- Tag/release/ruleset change: NO
- Worktree cleanup: NO
- Runtime implementation authority: NO
- Final state: WO-006 LOCAL ENABLING CANDIDATE - REVIEW REQUIRED
"@
    [System.IO.File]::WriteAllText($manifestPath, $manifest, $utf8NoBom)

    Write-Host "`n=== WO-006 LOCAL ENABLING RESULT ==="
    [pscustomobject]@{
        AuthoritativeBase = $baseMain
        ArchiveCommit = $archiveCommit
        ArchiveParent = $archiveParent
        ArchiveTree = $archiveTree
        ArchiveSubject = $archiveSubject
        ArchivePathCount = $archiveCommitted.Count
        EnablingCommit = $enablingCommit
        EnablingParent = $enablingParent
        EnablingTree = $enablingTree
        EnablingSubject = $enablingSubject
        EnablingPathCount = $enablingCommitted.Count
        LocalCommitCount = $commitCount
        MergeCommitCount = $mergeCount
        RuntimeChanges = 0
        TestChanges = 0
        BenchmarkChanges = 0
        DependencyChanges = 0
        CIChanges = 0
        LocalMain = $localMainAfter
        OriginMain = $originMainAfter
        LiveRemoteMain = $liveMainAfter
        PushPerformed = $false
        TagCreated = $false
        ReleaseCreated = $false
        RulesetChanged = $false
        WorktreeCleanupPerformed = $false
        SourceArchivePreserved = $true
        EnablingWorktreeClean = $true
        RuntimeImplementationAuthorized = $false
        Manifest = $manifestPath
        FinalStatus = "WO-006 LOCAL ENABLING CANDIDATE - REVIEW REQUIRED"
    } | Format-List

    Write-Host "Enabling governance paths:"
    $enablingCommitted | ForEach-Object { Write-Host " - $_" }
    Write-Host "`nWO-006 LOCAL ENABLING: COMPLETE"
    Write-Host "Two authorized local commits were created on $enablingBranch."
    Write-Host "No push, runtime, tests, benchmarks, tag, release, ruleset change, main modification, or worktree cleanup was performed."
}
catch {
    if (Test-Path -LiteralPath $enablingWorktree) {
        Write-Host "`nWO-006 enabling worktree preserved for diagnosis:"
        git -C $enablingWorktree status --short
    }
    throw
}
