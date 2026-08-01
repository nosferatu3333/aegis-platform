$ErrorActionPreference = "Stop"

if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$repo = "$env:USERPROFILE\Projects\aegis-platform"

$sourceWorktree = "$env:USERPROFILE\Projects\aegis-platform-wo-005"
$canonicalWorktree = "$env:USERPROFILE\Projects\aegis-platform-wo-005-candidate"
$reviewWorktree = "$env:USERPROFILE\Projects\aegis-platform-wo-005-review"

$canonicalBranch = "documentation/wo-005-environment-interaction-candidate"
$reviewBranch = "governance/wo-005-candidate-review"

$authoritativeBase = "be7502f73b51808d54728f912ead46ad0073c7b9"
$authorizationMain = "7a34c38d6210a2ed58f8966b3143ab67103424e4"

$sourceSubject = "Define WO-005 environment interaction specification"
$designationSubject = "Designate WO-005 candidate for review"

$traceabilityRelative = "governance/TRACEABILITY.md"
$workOrderRelative = "governance/work-orders/WO-005_ENVIRONMENT_INTERACTION_LAYER_SPECIFICATION.md"

$deliverablePaths = @(
    "docs/adr/ADR-006-environment-interaction-layer.md",
    "docs/architecture/environment-interaction-layer.md",
    "docs/specifications/v0.5-phase-b-environment-interaction-layer.md",
    "docs/roadmap/ROADMAP.md"
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
$manifestPath = Join-Path $logDirectory "WO-005-candidate-designation.txt"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Invoke-Native {
    param(
        [scriptblock]$Command,
        [string]$Label,
        [switch]$AllowExitOne
    )

    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    try {
        $output = @(& $Command)
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedPreference
    }

    if ($exitCode -ne 0 -and -not ($AllowExitOne -and $exitCode -eq 1)) {
        throw "$Label failed with exit code $exitCode."
    }

    return $output
}

function Get-LiveRemoteMain {
    param([string]$Repository)

    $lines = @(
        Invoke-Native {
            git -C $Repository ls-remote --heads origin refs/heads/main
        } "Live remote main lookup"
    )

    if ($lines.Count -ne 1) {
        throw "Expected exactly one live remote main reference."
    }

    return (($lines[0] -split "\s+")[0]).Trim()
}

function Get-ChangedPaths {
    param(
        [string]$Repository,
        [string]$Base,
        [string]$Head
    )

    return @(
        git -C $Repository diff --name-only $Base $Head
    )
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
            Write-Host "Unexpected:"
            $unexpected | ForEach-Object { Write-Host " - $_" }
        }

        if ($missing.Count -gt 0) {
            Write-Host "Missing:"
            $missing | ForEach-Object { Write-Host " - $_" }
        }

        throw "$Label path boundary mismatch."
    }
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

function Assert-WorktreeClean {
    param(
        [string]$Path,
        [string]$Label
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "$Label worktree path does not exist: $Path"
    }

    if (@(git -C $Path status --short).Count -ne 0) {
        throw "$Label worktree is not clean: $Path"
    }
}

function Assert-AllRegisteredWorktreesClean {
    param([string]$Repository)

    foreach ($item in @(Get-RegisteredWorktrees $Repository)) {
        Assert-WorktreeClean `
            -Path $item.Path `
            -Label "Registered"
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

Write-Host "`n=== WO-005 CANDIDATE DESIGNATION PREFLIGHT ==="

if (-not (Test-Path -LiteralPath $repo)) {
    throw "Repository not found: $repo"
}

Invoke-Native {
    git -C $repo fetch origin `
        "+refs/heads/main:refs/remotes/origin/main"
} "Remote main refresh" | Out-Null

$localMain = (git -C $repo rev-parse refs/heads/main).Trim()
$originMain = (
    git -C $repo rev-parse refs/remotes/origin/main
).Trim()
$liveMain = Get-LiveRemoteMain $repo

foreach ($identity in @($localMain, $originMain, $liveMain)) {
    if ($identity -ne $authorizationMain) {
        throw "Main identity differs from the WO-005 authorization commit."
    }
}

Assert-AllRegisteredWorktreesClean $repo
Assert-WorktreeClean `
    -Path $sourceWorktree `
    -Label "Source deliverable"

$sourceCommit = (
    git -C $sourceWorktree rev-parse HEAD
).Trim()

$sourceParent = (
    git -C $sourceWorktree rev-parse HEAD^
).Trim()

$sourceTree = (
    git -C $sourceWorktree rev-parse "HEAD^{tree}"
).Trim()

$sourceCommitSubject = (
    git -C $sourceWorktree log -1 --format=%s
).Trim()

if ($sourceCommitSubject -ne $sourceSubject) {
    throw "Unexpected source deliverable subject: $sourceCommitSubject"
}

if ($sourceParent -ne $authorizationMain) {
    throw "The source deliverable parent is not the WO-005 authorization commit."
}

$sourceChangedPaths = @(
    git -C $sourceWorktree diff-tree `
        --no-commit-id `
        --name-only `
        -r `
        HEAD
)

Assert-ExactPathSet `
    -Actual $sourceChangedPaths `
    -Expected $deliverablePaths `
    -Label "Source deliverable commit"

Invoke-Native {
    git -C $sourceWorktree diff-tree `
        --check `
        $sourceParent `
        $sourceCommit
} "Source deliverable whitespace validation" | Out-Null

Write-Host "Source deliverable identity and four-document boundary: PASS"
Write-Host "Source commit: $sourceCommit"
Write-Host "Source parent: $sourceParent"

Write-Host "`n=== RECONSTRUCT CANONICAL FOUR-DOCUMENT CANDIDATE ==="

if (Test-Path -LiteralPath $canonicalWorktree) {
    throw "Canonical candidate worktree already exists: $canonicalWorktree"
}

if (@(git -C $repo branch --list $canonicalBranch).Count -ne 0) {
    throw "Canonical candidate branch already exists: $canonicalBranch"
}

Invoke-Native {
    git -C $repo worktree add `
        -b $canonicalBranch `
        $canonicalWorktree `
        $authoritativeBase
} "Canonical candidate worktree creation" | Out-Null

try {
    Invoke-Native {
        git -C $canonicalWorktree cherry-pick $sourceCommit
    } "Canonical candidate reconstruction" | Out-Null
}
catch {
    if (
        Test-Path -LiteralPath (
            Join-Path $canonicalWorktree ".git\CHERRY_PICK_HEAD"
        )
    ) {
        git -C $canonicalWorktree cherry-pick --abort | Out-Null
    }

    throw
}

$canonicalCommit = (
    git -C $canonicalWorktree rev-parse HEAD
).Trim()

$canonicalParent = (
    git -C $canonicalWorktree rev-parse HEAD^
).Trim()

$canonicalTree = (
    git -C $canonicalWorktree rev-parse "HEAD^{tree}"
).Trim()

$canonicalSubject = (
    git -C $canonicalWorktree log -1 --format=%s
).Trim()

if ($canonicalParent -ne $authoritativeBase) {
    throw "Canonical candidate parent mismatch."
}

if ($canonicalSubject -ne $sourceSubject) {
    throw "Canonical candidate subject mismatch."
}

$canonicalChangedPaths = Get-ChangedPaths `
    -Repository $canonicalWorktree `
    -Base $authoritativeBase `
    -Head $canonicalCommit

Assert-ExactPathSet `
    -Actual $canonicalChangedPaths `
    -Expected $deliverablePaths `
    -Label "Canonical candidate"

Invoke-Native {
    git -C $canonicalWorktree diff `
        --check `
        $authoritativeBase `
        $canonicalCommit
} "Canonical candidate whitespace validation" | Out-Null

foreach ($path in $deliverablePaths) {
    $sourceBlob = (
        git -C $sourceWorktree rev-parse "${sourceCommit}:$path"
    ).Trim()

    $canonicalBlob = (
        git -C $canonicalWorktree rev-parse "${canonicalCommit}:$path"
    ).Trim()

    if ($sourceBlob -ne $canonicalBlob) {
        throw "Document content identity mismatch: $path"
    }
}

$forbiddenChanges = @(
    git -C $canonicalWorktree diff `
        --name-only `
        $authoritativeBase `
        $canonicalCommit `
        -- `
        aegis_os `
        tests `
        pyproject.toml `
        .github
)

if ($forbiddenChanges.Count -ne 0) {
    throw "Canonical candidate contains forbidden executable, test, dependency, or CI changes."
}

Assert-WorktreeClean `
    -Path $canonicalWorktree `
    -Label "Canonical candidate"

Write-Host "Canonical candidate base and document content identity: PASS"
Write-Host "Canonical candidate: $canonicalCommit"
Write-Host "Canonical parent: $canonicalParent"
Write-Host "Canonical tree: $canonicalTree"

Write-Host "`n=== CREATE GOVERNANCE REVIEW WORKTREE ==="

if (Test-Path -LiteralPath $reviewWorktree) {
    throw "WO-005 review worktree already exists: $reviewWorktree"
}

if (@(git -C $repo branch --list $reviewBranch).Count -ne 0) {
    throw "WO-005 review branch already exists: $reviewBranch"
}

Invoke-Native {
    git -C $repo worktree add `
        -b $reviewBranch `
        $reviewWorktree `
        $authorizationMain
} "WO-005 review worktree creation" | Out-Null

$workOrderPath = Join-Path $reviewWorktree $workOrderRelative
$traceabilityPath = Join-Path $reviewWorktree $traceabilityRelative

Write-Host "`n=== RECORD CANDIDATE DESIGNATION ==="

$workOrder = [System.IO.File]::ReadAllText($workOrderPath)
$workOrder = $workOrder -replace "`r`n", "`n"

if ($workOrder.Contains("## Candidate designation")) {
    throw "WO-005 already contains a candidate designation."
}

$workOrder = Replace-ExactlyOnce `
    -Text $workOrder `
    -OldValue "**Status:** ACTIVE - ARCHITECTURE AND SPECIFICATION WORK AUTHORIZED" `
    -NewValue "**Status:** ACTIVE - CANDIDATE DESIGNATED FOR REVIEW" `
    -Label "WO-005 status"

$oldDisposition = @'
WO-005: ACTIVE - ARCHITECTURE AND SPECIFICATION WORK AUTHORIZED
Authoritative base: be7502f73b51808d54728f912ead46ad0073c7b9
Deliverable scope: FOUR DOCUMENTATION PATHS
Deliverable candidate designated: NO
Architecture review: NOT STARTED
QA review: NOT STARTED
Deliverable integration authority: NOT GRANTED
Deliverable publication authority: NOT GRANTED
Runtime implementation authority: NOT GRANTED
'@

$newDisposition = @"
WO-005: ACTIVE - CANDIDATE DESIGNATED FOR REVIEW
Authoritative base: be7502f73b51808d54728f912ead46ad0073c7b9
Authorization main: 7a34c38d6210a2ed58f8966b3143ab67103424e4
Deliverable scope: FOUR DOCUMENTATION PATHS
Deliverable candidate designated: $canonicalCommit
Candidate tree: $canonicalTree
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

$candidateSection = @"

## Candidate designation

- Designation date: 2026-07-31
- Authoritative base: ``$authoritativeBase``
- Published authorization main: ``$authorizationMain``
- Source deliverable commit: ``$sourceCommit``
- Source deliverable parent: ``$sourceParent``
- Canonical reviewed candidate: ``$canonicalCommit``
- Canonical candidate parent: ``$canonicalParent``
- Canonical candidate tree: ``$canonicalTree``
- Candidate subject: ``$canonicalSubject``
- Changed-path count: 4
- Executable-code changes: 0
- Test changes: 0
- Dependency changes: 0
- CI changes: 0
- Candidate worktree clean: yes
- Source-to-canonical document blob identity: pass
- Architecture review: pending
- QA review: pending
- Integration authority: not granted
- Publication authority: not granted
- Runtime implementation authority: not granted

### Canonical changed paths

1. ``docs/adr/ADR-006-environment-interaction-layer.md``
2. ``docs/architecture/environment-interaction-layer.md``
3. ``docs/specifications/v0.5-phase-b-environment-interaction-layer.md``
4. ``docs/roadmap/ROADMAP.md``

### Designation rationale

The initial local deliverable was created above the published WO-005
authorization commit. The canonical candidate was reconstructed from the exact
architectural base by replaying only the four-document deliverable commit.

All four document blobs are identical between the source deliverable and the
canonical candidate. The canonical candidate therefore preserves the authored
content while satisfying the exact base-to-candidate path boundary.

This designation authorizes review of the immutable canonical candidate only.
It does not authorize correction, integration, publication, runtime
implementation, push, main modification, tag, release, ruleset change, or
cleanup.
"@

$workOrder = $workOrder.TrimEnd() + $candidateSection + "`n"

$traceability = [System.IO.File]::ReadAllText($traceabilityPath)
$traceability = $traceability -replace "`r`n", "`n"

if ($traceability.Contains("## TR-008 WO-005 Candidate Designation")) {
    throw "TR-008 candidate designation already exists."
}

$traceabilitySection = @"

## TR-008 WO-005 Candidate Designation

- Work order: WO-005 - Environment Interaction Layer Architecture Acceptance and Implementation Specification
- Designation date: 2026-07-31
- Authoritative base: ``$authoritativeBase``
- Published authorization main: ``$authorizationMain``
- Source deliverable: ``$sourceCommit``
- Canonical reviewed candidate: ``$canonicalCommit``
- Canonical parent: ``$canonicalParent``
- Canonical tree: ``$canonicalTree``
- Candidate changed paths: exactly four authorized documentation paths
- Source-to-canonical document identity: **PASS**
- Executable, test, dependency, and CI changes: none
- Candidate state: **DESIGNATED FOR REVIEW**
- Architecture review: pending
- QA review: pending
- Integration authority: not granted
- Publication authority: not granted
- Runtime implementation authority: not granted

The designated candidate is the canonical commit reconstructed directly from
the exact architectural base. Review must evaluate this immutable SHA and tree.
Any content correction creates a new candidate and requires redesignation.
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
    -Label "Candidate designation governance"

Invoke-Native {
    git -C $reviewWorktree diff --check
} "Candidate designation whitespace validation" | Out-Null

Write-Host "Exact two-path governance designation boundary: PASS"

Write-Host "`n=== COMMIT CANDIDATE DESIGNATION ==="

Invoke-Native {
    git -C $reviewWorktree add -- $governancePaths
} "Candidate designation staging" | Out-Null

$stagedPaths = @(
    git -C $reviewWorktree diff --cached --name-only
)

Assert-ExactPathSet `
    -Actual $stagedPaths `
    -Expected $governancePaths `
    -Label "Staged candidate designation"

Invoke-Native {
    git -C $reviewWorktree diff --cached --check
} "Staged designation whitespace validation" | Out-Null

Invoke-Native {
    git -C $reviewWorktree commit -m $designationSubject
} "Candidate designation commit creation" | Out-Null

$designationCommit = (
    git -C $reviewWorktree rev-parse HEAD
).Trim()

$designationParent = (
    git -C $reviewWorktree rev-parse HEAD^
).Trim()

$designationTree = (
    git -C $reviewWorktree rev-parse "HEAD^{tree}"
).Trim()

if ($designationParent -ne $authorizationMain) {
    throw "Candidate designation parent mismatch."
}

$designationCommittedPaths = @(
    git -C $reviewWorktree diff-tree `
        --no-commit-id `
        --name-only `
        -r `
        HEAD
)

Assert-ExactPathSet `
    -Actual $designationCommittedPaths `
    -Expected $governancePaths `
    -Label "Committed candidate designation"

Assert-WorktreeClean `
    -Path $reviewWorktree `
    -Label "Review governance"

Write-Host "Governance candidate designation commit: CREATED"

Write-Host "`n=== FINAL PRESERVATION AND MANIFEST ==="

Invoke-Native {
    git -C $repo fetch origin `
        "+refs/heads/main:refs/remotes/origin/main"
} "Final remote refresh" | Out-Null

$finalLocalMain = (git -C $repo rev-parse refs/heads/main).Trim()
$finalOriginMain = (
    git -C $repo rev-parse refs/remotes/origin/main
).Trim()
$finalLiveMain = Get-LiveRemoteMain $repo

foreach ($identity in @(
    $finalLocalMain,
    $finalOriginMain,
    $finalLiveMain
)) {
    if ($identity -ne $authorizationMain) {
        throw "Main or remote changed during candidate designation."
    }
}

Assert-AllRegisteredWorktreesClean $repo

New-Item `
    -ItemType Directory `
    -Path $logDirectory `
    -Force | Out-Null

$manifest = @"
AEGIS WO-005 Candidate Designation
==================================

Date: 2026-07-31

Authoritative architectural base:
$authoritativeBase

Published WO-005 authorization main:
$authorizationMain

Source deliverable:
Commit: $sourceCommit
Parent: $sourceParent
Tree: $sourceTree
Worktree: $sourceWorktree

Canonical designated candidate:
Commit: $canonicalCommit
Parent: $canonicalParent
Tree: $canonicalTree
Branch: $canonicalBranch
Worktree: $canonicalWorktree
Subject: $canonicalSubject

Governance designation:
Commit: $designationCommit
Parent: $designationParent
Tree: $designationTree
Branch: $reviewBranch
Worktree: $reviewWorktree
Subject: $designationSubject

Changed deliverable paths:
$($deliverablePaths -join "`r`n")

Validation:
- Exact four-document boundary: PASS
- Source-to-canonical document blob identity: PASS
- Executable code changes: 0
- Test changes: 0
- Dependency changes: 0
- CI changes: 0
- Whitespace validation: PASS
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

Write-Host "`n=== WO-005 CANDIDATE DESIGNATION RESULT ==="

[pscustomobject]@{
    AuthoritativeBase = $authoritativeBase
    AuthorizationMain = $authorizationMain
    SourceDeliverableCommit = $sourceCommit
    SourceDeliverableParent = $sourceParent
    CanonicalCandidate = $canonicalCommit
    CanonicalCandidateParent = $canonicalParent
    CanonicalCandidateTree = $canonicalTree
    CanonicalPathCount = $canonicalChangedPaths.Count
    DocumentContentIdentity = "PASS"
    ExecutableCodeChanges = 0
    TestChanges = 0
    DependencyChanges = 0
    CIChanges = 0
    DesignationCommit = $designationCommit
    DesignationParent = $designationParent
    DesignationTree = $designationTree
    GovernancePathCount = $designationCommittedPaths.Count
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
    FinalStatus = "WO-005 CANDIDATE DESIGNATED FOR REVIEW"
} | Format-List

Write-Host "Canonical deliverable paths:"
$canonicalChangedPaths | ForEach-Object { Write-Host " - $_" }

Write-Host "`nWO-005 CANDIDATE DESIGNATION: COMPLETE"
Write-Host "The canonical four-document candidate is designated for review."
Write-Host "No push, main update, integration, runtime implementation, tag, release, ruleset change, or cleanup was performed."
