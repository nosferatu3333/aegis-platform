$ErrorActionPreference = "Stop"

if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$repo = "$env:USERPROFILE\Projects\aegis-platform"
$worktree = "$env:USERPROFILE\Projects\aegis-platform-wo-005-amendment-local-fix"
$branch = "governance/wo-005-preexisting-specification-amendment-local-fix"

$expectedMain = "7a34c38d6210a2ed58f8966b3143ab67103424e4"
$architecturalBase = "be7502f73b51808d54728f912ead46ad0073c7b9"
$commitSubject = "Amend WO-005 for pre-existing Phase B specification"

$workOrderRelative = "governance/work-orders/WO-005_ENVIRONMENT_INTERACTION_LAYER_SPECIFICATION.md"
$traceabilityRelative = "governance/TRACEABILITY.md"
$specRelative = "docs/specifications/v0.5-phase-b-environment-interaction-layer.md"

$expectedPaths = @(
    $traceabilityRelative,
    $workOrderRelative
)

$technicalPaths = @(
    "docs/adr/ADR-006-environment-interaction-layer.md",
    "docs/architecture/environment-interaction-layer.md",
    $specRelative,
    "docs/roadmap/ROADMAP.md"
)

$operationsRoot = [Environment]::GetEnvironmentVariable(
    "AEGIS_OPERATIONS",
    "User"
)

if ([string]::IsNullOrWhiteSpace($operationsRoot)) {
    $operationsRoot = "$env:USERPROFILE\Projects\AEGIS-operations"
}

$logDirectory = Join-Path $operationsRoot "logs\WO-005"
$manifestPath = Join-Path $logDirectory "WO-005-governance-amendment.txt"
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

function Move-LocalMainFastForward {
    param(
        [string]$Repository,
        [string]$ExpectedOld,
        [string]$Target
    )

    $currentMain = (
        git -C $Repository rev-parse refs/heads/main
    ).Trim()

    if ($currentMain -eq $Target) {
        return
    }

    if ($currentMain -ne $ExpectedOld) {
        throw "Local main has an unexpected value: $currentMain"
    }

    Invoke-Native {
        git -C $Repository merge-base `
            --is-ancestor `
            $currentMain `
            $Target
    } "Local-main fast-forward ancestry" | Out-Null

    $mainWorktrees = @(
        Get-RegisteredWorktrees $Repository |
            Where-Object { $_.Branch -eq "refs/heads/main" }
    )

    if ($mainWorktrees.Count -gt 1) {
        throw "Main is checked out in more than one worktree."
    }

    if ($mainWorktrees.Count -eq 1) {
        if (@(git -C $mainWorktrees[0].Path status --short).Count -ne 0) {
            throw "The checked-out main worktree is not clean."
        }

        Invoke-Native {
            git -C $mainWorktrees[0].Path merge --ff-only $Target
        } "Checked-out local main synchronization" | Out-Null
    }
    else {
        Invoke-Native {
            git -C $Repository branch -f main $Target
        } "Local main reference synchronization" | Out-Null
    }

    if (
        (git -C $Repository rev-parse refs/heads/main).Trim() -ne
        $Target
    ) {
        throw "Local main synchronization failed."
    }
}

Write-Host "`n=== WO-005 GOVERNANCE AMENDMENT PREFLIGHT ==="

if (-not (Test-Path -LiteralPath $repo)) {
    throw "Repository not found: $repo"
}

Invoke-Native {
    git -C $repo fetch origin `
        "+refs/heads/main:refs/remotes/origin/main"
} "Remote main refresh" | Out-Null

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
    if ($identity -ne $expectedMain) {
        throw "Main identity differs from the published WO-005 authorization commit."
    }
}

Assert-AllWorktreesClean `
    -Repository $repo `
    -Label "Preflight"

if (Test-Path -LiteralPath $worktree) {
    throw "WO-005 amendment worktree already exists: $worktree"
}

if (@(git -C $repo branch --list $branch).Count -ne 0) {
    throw "WO-005 amendment branch already exists: $branch"
}

$specAtArchitecturalBase = @(
    git -C $repo ls-tree `
        -r `
        --name-only `
        $architecturalBase `
        -- `
        $specRelative
)

if ($LASTEXITCODE -ne 0) {
    throw "Unable to inspect the Phase B specification at the architectural base."
}

if (
    $specAtArchitecturalBase.Count -ne 1 -or
    $specAtArchitecturalBase[0] -ne $specRelative
) {
    throw "The pre-existing Phase B specification was not found at the architectural base."
}

$specStatus = @(
    git -C $repo show `
        "${architecturalBase}:${specRelative}"
) -join "`n"

if ($LASTEXITCODE -ne 0) {
    throw "Unable to read the pre-existing Phase B specification."
}

if (-not $specStatus.Contains("Proposed implementation specification")) {
    throw "The expected proposed Phase B specification status was not found."
}

Write-Host "Main identity, clean worktrees, and pre-existing specification evidence: PASS"

Write-Host "`n=== CREATE AMENDMENT WORKTREE ==="

Invoke-Native {
    git -C $repo worktree add `
        -b $branch `
        $worktree `
        $expectedMain
} "WO-005 amendment worktree creation" | Out-Null

$workOrderPath = Join-Path $worktree $workOrderRelative
$traceabilityPath = Join-Path $worktree $traceabilityRelative

try {
    Write-Host "`n=== AMEND WO-005 GOVERNANCE ==="

    $workOrder = [System.IO.File]::ReadAllText($workOrderPath)
    $workOrder = $workOrder -replace "`r`n", "`n"

    if ($workOrder.Contains("## Amendment 001 - Pre-existing specification correction")) {
        throw "WO-005 Amendment 001 already exists."
    }

    $workOrder = Replace-ExactlyOnce `
        -Text $workOrder `
        -OldValue "**Status:** ACTIVE - ARCHITECTURE AND SPECIFICATION WORK AUTHORIZED" `
        -NewValue "**Status:** ACTIVE - ARCHITECTURE AND PRE-EXISTING SPECIFICATION REVISION AUTHORIZED" `
        -Label "WO-005 status"

    $oldAuthorizationBasis = @'
The current roadmap identifies v0.5 Phase B as the next planned platform
increment. The architecture document and ADR-006 are proposed and explicitly
require an implementation specification before runtime implementation.

WO-005 authorizes only the bounded documentation and specification work needed
to remove those open implementation decisions.
'@

    $newAuthorizationBasis = @'
The current roadmap identifies v0.5 Phase B as the next planned platform
increment. The architecture document and ADR-006 are proposed. A detailed
Phase B implementation specification already exists at the authoritative base
with status `Proposed implementation specification`.

WO-005 authorizes only the bounded documentation work needed to review,
reconcile, revise, and accept the pre-existing specification together with
ADR-006, the architecture document, and the roadmap. It does not authorize
creation of a replacement specification or runtime implementation.
'@

    $workOrder = Replace-ExactlyOnce `
        -Text $workOrder `
        -OldValue $oldAuthorizationBasis `
        -NewValue $newAuthorizationBasis `
        -Label "WO-005 authorization basis"

    $workOrder = Replace-ExactlyOnce `
        -Text $workOrder `
        -OldValue '3. `docs/specifications/v0.5-phase-b-environment-interaction-layer.md` - new' `
        -NewValue '3. `docs/specifications/v0.5-phase-b-environment-interaction-layer.md` - existing proposed specification; bounded revision authorized' `
        -Label "WO-005 specification path status"

    $workOrder = Replace-ExactlyOnce `
        -Text $workOrder `
        -OldValue "3. create the complete Phase B implementation specification;" `
        -NewValue "3. review, reconcile, and revise the existing Phase B implementation specification into an accepted implementation-ready state;" `
        -Label "WO-005 required deliverable content"

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

    $newDisposition = @'
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

    $workOrder = Replace-ExactlyOnce `
        -Text $workOrder `
        -OldValue $oldDisposition `
        -NewValue $newDisposition.TrimEnd() `
        -Label "WO-005 current disposition"

    $amendmentSection = @'

## Amendment 001 - Pre-existing specification correction

- Amendment date: 2026-07-31
- Amendment authority: explicit Product Owner / Founder authorization
- Published authorization commit amended: `7a34c38d6210a2ed58f8966b3143ab67103424e4`
- Architectural base inspected: `be7502f73b51808d54728f912ead46ad0073c7b9`
- Existing specification: `docs/specifications/v0.5-phase-b-environment-interaction-layer.md`
- Existing specification state: `Proposed implementation specification`
- Amendment paths: governance records only
- Runtime implementation: not authorized
- Technical-document modification by this amendment: none

### Correction

The original WO-005 authorization incorrectly described the Phase B
implementation specification as a new file and required its creation.

The specification already exists at the exact authoritative architectural base.
WO-005 therefore authorizes bounded review, reconciliation, revision, and
acceptance of that existing proposed specification. It does not authorize
replacement with an unrelated document.

### Corrected deliverable interpretation

The four authorized deliverable paths remain unchanged. All four are existing
documents at the architectural base:

1. `docs/adr/ADR-006-environment-interaction-layer.md`
2. `docs/architecture/environment-interaction-layer.md`
3. `docs/specifications/v0.5-phase-b-environment-interaction-layer.md`
4. `docs/roadmap/ROADMAP.md`

A candidate must compare directly against
`be7502f73b51808d54728f912ead46ad0073c7b9` and may revise only these four
existing documents.

### Preservation boundary

This amendment changes governance records only. It grants no authority to
modify technical documents during the amendment, implement runtime code,
change tests, integrate a deliverable, publish a deliverable, create tags or
releases, alter rulesets, or perform cleanup.
'@

    $workOrder = $workOrder.TrimEnd() + $amendmentSection + "`n"

    $traceability = [System.IO.File]::ReadAllText($traceabilityPath)
    $traceability = $traceability -replace "`r`n", "`n"

    if ($traceability.Contains("## TR-008 WO-005 Governance Amendment 001")) {
        throw "TR-008 WO-005 Governance Amendment 001 already exists."
    }

    $traceability = Replace-ExactlyOnce `
        -Text $traceability `
        -OldValue "ADR-006, the Phase B architecture, the roadmap, and a new implementation`nspecification only within the exact documented boundary." `
        -NewValue "ADR-006, the Phase B architecture, the roadmap, and the pre-existing proposed`nimplementation specification only within the exact documented boundary." `
        -Label "TR-007 specification status"

    $traceabilitySection = @'

## TR-008 WO-005 Governance Amendment 001

- Work order: WO-005 - Environment Interaction Layer Architecture Acceptance and Implementation Specification
- Amendment date: 2026-07-31
- Amended authorization commit: `7a34c38d6210a2ed58f8966b3143ab67103424e4`
- Architectural base: `be7502f73b51808d54728f912ead46ad0073c7b9`
- Verified existing specification: `docs/specifications/v0.5-phase-b-environment-interaction-layer.md`
- Verified base status: `Proposed implementation specification`
- Correction: specification is pre-existing; bounded revision replaces creation
- Amendment boundary: exactly two governance paths
- Technical-document changes: none
- Runtime implementation: not authorized
- Deliverable integration: not authorized
- Deliverable publication: not authorized
- Amendment publication authority: granted for this governance commit only

The four-path deliverable boundary is unchanged. A future candidate must revise
the existing ADR, architecture, specification, and roadmap directly from the
exact architectural base. This amendment grants no additional technical,
integration, publication, release, ruleset, or cleanup authority.
'@

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

    Write-Host "WO-005 work order and traceability correction: WRITTEN"

    Write-Host "`n=== VALIDATE AMENDMENT BOUNDARY ==="

    $changedPaths = @(
        git -C $worktree status --short |
            ForEach-Object { $_.Substring(3) }
    )

    Assert-ExactPathSet `
        -Actual $changedPaths `
        -Expected $expectedPaths `
        -Label "WO-005 amendment"

    Invoke-Native {
        git -C $worktree diff --check
    } "WO-005 amendment whitespace validation" | Out-Null

    $technicalChanges = @(
        git -C $worktree diff `
            --name-only `
            $expectedMain `
            -- `
            $technicalPaths
    )

    if ($technicalChanges.Count -ne 0) {
        throw "The governance amendment changed technical documents."
    }

    $finalWorkOrderText = [System.IO.File]::ReadAllText($workOrderPath)
    $finalTraceabilityText = [System.IO.File]::ReadAllText($traceabilityPath)

    foreach ($requiredText in @(
        "PRE-EXISTING SPECIFICATION REVISION AUTHORIZED",
        "existing proposed specification; bounded revision authorized",
        "Amendment 001 - Pre-existing specification correction",
        "replacement with an unrelated document"
    )) {
        if (-not $finalWorkOrderText.Contains($requiredText)) {
            throw "Required amended work-order text is missing: $requiredText"
        }
    }

    foreach ($requiredText in @(
        "## TR-008 WO-005 Governance Amendment 001",
        "specification is pre-existing; bounded revision replaces creation",
        "Technical-document changes: none"
    )) {
        if (-not $finalTraceabilityText.Contains($requiredText)) {
            throw "Required amended traceability text is missing: $requiredText"
        }
    }

    Write-Host "Exact two-path governance boundary and zero technical changes: PASS"

    Write-Host "`n=== COMMIT GOVERNANCE AMENDMENT ==="

    Invoke-Native {
        git -C $worktree add -- $expectedPaths
    } "WO-005 amendment staging" | Out-Null

    $stagedPaths = @(
        git -C $worktree diff --cached --name-only
    )

    Assert-ExactPathSet `
        -Actual $stagedPaths `
        -Expected $expectedPaths `
        -Label "Staged WO-005 amendment"

    Invoke-Native {
        git -C $worktree diff --cached --check
    } "Staged WO-005 amendment validation" | Out-Null

    Invoke-Native {
        git -C $worktree commit -m $commitSubject
    } "WO-005 amendment commit creation" | Out-Null

    $amendmentCommit = (
        git -C $worktree rev-parse HEAD
    ).Trim()

    $amendmentParent = (
        git -C $worktree rev-parse HEAD^
    ).Trim()

    $amendmentTree = (
        git -C $worktree rev-parse "HEAD^{tree}"
    ).Trim()

    $amendmentSubject = (
        git -C $worktree log -1 --format=%s
    ).Trim()

    if ($amendmentParent -ne $expectedMain) {
        throw "WO-005 amendment commit parent mismatch."
    }

    if ($amendmentSubject -ne $commitSubject) {
        throw "WO-005 amendment commit subject mismatch."
    }

    $committedPaths = @(
        git -C $worktree diff-tree `
            --no-commit-id `
            --name-only `
            -r `
            HEAD
    )

    Assert-ExactPathSet `
        -Actual $committedPaths `
        -Expected $expectedPaths `
        -Label "Committed WO-005 amendment"

    if (@(git -C $worktree status --short).Count -ne 0) {
        throw "WO-005 amendment worktree is not clean after commit."
    }

    Write-Host "Governance-only amendment commit: CREATED"

    Write-Host "`n=== STRICT FAST-FORWARD PUBLICATION ==="

    Invoke-Native {
        git -C $repo fetch origin `
            "+refs/heads/main:refs/remotes/origin/main"
    } "Pre-publication remote refresh" | Out-Null

    $originImmediatelyBefore = (
        git -C $repo rev-parse refs/remotes/origin/main
    ).Trim()

    $liveImmediatelyBefore = Get-LiveRemoteMain $repo

    if (
        $originImmediatelyBefore -ne $expectedMain -or
        $liveImmediatelyBefore -ne $expectedMain
    ) {
        throw "Remote main changed before amendment publication."
    }

    Invoke-Native {
        git -C $worktree merge-base `
            --is-ancestor `
            $expectedMain `
            $amendmentCommit
    } "Amendment fast-forward ancestry validation" | Out-Null

    Assert-AllWorktreesClean `
        -Repository $repo `
        -Label "Pre-publication"

    Invoke-Native {
        git -C $worktree push `
            --porcelain `
            origin `
            "${amendmentCommit}:refs/heads/main"
    } "WO-005 amendment fast-forward push" | Out-Null

    Write-Host "WO-005 governance amendment fast-forward push: COMPLETE"

    Write-Host "`n=== VERIFY AND SYNCHRONIZE MAIN ==="

    Invoke-Native {
        git -C $repo fetch origin `
            "+refs/heads/main:refs/remotes/origin/main"
    } "Post-publication remote refresh" | Out-Null

    $liveAfter = Get-LiveRemoteMain $repo
    $originAfter = (
        git -C $repo rev-parse refs/remotes/origin/main
    ).Trim()

    if ($liveAfter -ne $amendmentCommit) {
        throw "Live remote main does not match the amendment commit."
    }

    if ($originAfter -ne $amendmentCommit) {
        throw "origin/main does not match the amendment commit."
    }

    Move-LocalMainFastForward `
        -Repository $repo `
        -ExpectedOld $expectedMain `
        -Target $amendmentCommit

    $localMainAfter = (
        git -C $repo rev-parse refs/heads/main
    ).Trim()

    if ($localMainAfter -ne $amendmentCommit) {
        throw "Local main does not match the amendment commit."
    }

    Write-Host "Remote, origin/main, and local main identity: PASS"

    Write-Host "`n=== FINAL PRESERVATION AND MANIFEST ==="

    Assert-AllWorktreesClean `
        -Repository $repo `
        -Label "Final"

    $finalTechnicalDelta = @(
        git -C $repo diff `
            --name-only `
            $expectedMain `
            $amendmentCommit `
            -- `
            $technicalPaths `
            aegis_os `
            tests `
            pyproject.toml `
            .github
    )

    if ($finalTechnicalDelta.Count -ne 0) {
        throw "Published amendment includes unauthorized technical changes."
    }

    New-Item `
        -ItemType Directory `
        -Path $logDirectory `
        -Force | Out-Null

    $manifest = @"
AEGIS WO-005 Governance Amendment 001
=====================================

Date: 2026-07-31

Previous main:
$expectedMain

Amendment commit:
$amendmentCommit

Amendment parent:
$amendmentParent

Amendment tree:
$amendmentTree

Subject:
$amendmentSubject

Changed paths:
$($committedPaths -join "`r`n")

Verified pre-existing specification:
$specRelative

Architectural base:
$architecturalBase

Validation:
- Existing specification at architectural base: PASS
- Existing status Proposed implementation specification: PASS
- Exact governance path count: 2
- Technical-document changes: 0
- Runtime changes: 0
- Test changes: 0
- Dependency changes: 0
- CI changes: 0
- Strict fast-forward publication: PASS
- Force-push: NO
- Merge commit: NO
- Tag or release: NONE
- Worktrees clean: PASS
- Runtime implementation authority: NO
- Deliverable integration authority: NO
- Deliverable publication authority: NO
"@

    [System.IO.File]::WriteAllText(
        $manifestPath,
        $manifest,
        $utf8NoBom
    )

    Write-Host "`n=== WO-005 GOVERNANCE AMENDMENT RESULT ==="

    [pscustomobject]@{
        PreviousMain = $expectedMain
        ArchitecturalBase = $architecturalBase
        PreExistingSpecification = $specRelative
        VerifiedSpecificationStatus = "PROPOSED IMPLEMENTATION SPECIFICATION"
        AmendmentCommit = $amendmentCommit
        AmendmentParent = $amendmentParent
        AmendmentTree = $amendmentTree
        AmendmentSubject = $amendmentSubject
        AmendmentPathCount = $committedPaths.Count
        TechnicalDocumentChanges = 0
        RuntimeChanges = 0
        TestChanges = 0
        DependencyChanges = 0
        CIChanges = 0
        LiveRemoteMain = $liveAfter
        OriginMain = $originAfter
        LocalMain = $localMainAfter
        PushType = "STRICT FAST-FORWARD"
        ForcePush = $false
        MergeCommit = $false
        TagCreated = $false
        ReleaseCreated = $false
        WorktreesClean = $true
        Manifest = $manifestPath
        RuntimeImplementationAuthorized = $false
        DeliverableIntegrationAuthorized = $false
        DeliverablePublicationAuthorized = $false
        FinalStatus = "WO-005 GOVERNANCE AMENDMENT PUBLISHED"
    } | Format-List

    Write-Host "Amendment paths:"
    $committedPaths | ForEach-Object { Write-Host " - $_" }

    Write-Host "`nWO-005 GOVERNANCE AMENDMENT: COMPLETE"
    Write-Host "The pre-existing Phase B specification status is corrected in governance."
    Write-Host "No technical document, runtime, test, dependency, CI, tag, release, ruleset, or cleanup change was performed."
}
catch {
    if (Test-Path -LiteralPath $worktree) {
        Write-Host "`nWO-005 amendment worktree preserved for diagnosis:"
        git -C $worktree status --short
    }

    throw
}
