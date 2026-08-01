$ErrorActionPreference = "Stop"

if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$repo = "$env:USERPROFILE\Projects\aegis-platform"
$closureWorktree = "$env:USERPROFILE\Projects\aegis-platform-wo-005-closure"
$closureBranch = "governance/wo-005-closure"

$publishedMain = "7463aa6701a2246d9035476c7355007cb7051574"
$preIntegrationMain = "ad743b4568bbd82527f7ff192c5b10ca4d59c2e9"
$architecturalBase = "be7502f73b51808d54728f912ead46ad0073c7b9"

$technicalIntegrated = "5575031e4c2e0d7c7bf4a10d0e2d3558fcf406a7"
$designationIntegrated = "7ecd4938a63e7b51c06cf5a0c11f39f2ab615822"
$architectureReviewIntegrated = "98f1c506d8d1d19a092b71b81577220a42e874a2"
$qaReviewIntegrated = "dd75c5b458fd37a64646736066e20efe4f3fc01b"
$finalVerdictIntegrated = "7463aa6701a2246d9035476c7355007cb7051574"

$closureSubject = "Close WO-005 after main publication"

$workOrderRelative = "governance/work-orders/WO-005_ENVIRONMENT_INTERACTION_LAYER_SPECIFICATION.md"
$traceabilityRelative = "governance/TRACEABILITY.md"

$closurePaths = @(
    $traceabilityRelative,
    $workOrderRelative
)

$publishedPaths = @(
    "docs/adr/ADR-006-environment-interaction-layer.md",
    "docs/architecture/environment-interaction-layer.md",
    "docs/roadmap/ROADMAP.md",
    "docs/specifications/v0.5-phase-b-environment-interaction-layer.md",
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
$manifestPath = Join-Path $logDirectory "WO-005-closure.txt"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Invoke-Native {
    param(
        [scriptblock]$Command,
        [string]$Label
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

    if ($exitCode -ne 0) {
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

function Get-RemoteSnapshot {
    param([string]$Repository)

    return @(
        Invoke-Native {
            git -C $Repository ls-remote --heads --tags origin
        } "Remote reference snapshot" |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_ } |
            Sort-Object
    )
}

function Get-NonMainRemoteSnapshot {
    param([string[]]$Snapshot)

    return @(
        $Snapshot |
            Where-Object {
                ($_ -split "\s+", 2)[1] -ne "refs/heads/main"
            } |
            Sort-Object
    )
}

function Assert-SequenceEqual {
    param(
        [string[]]$Before,
        [string[]]$After,
        [string]$Label
    )

    if ($Before.Count -ne $After.Count) {
        throw "$Label count changed from $($Before.Count) to $($After.Count)."
    }

    for ($index = 0; $index -lt $Before.Count; $index++) {
        if ($Before[$index] -ne $After[$index]) {
            Write-Host "$Label mismatch:"
            Write-Host "Before: $($Before[$index])"
            Write-Host "After : $($After[$index])"
            throw "$Label changed."
        }
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
            $ExpectedOld `
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
        $mainPath = $mainWorktrees[0].Path

        if (@(git -C $mainPath status --short).Count -ne 0) {
            throw "The checked-out main worktree is not clean."
        }

        Invoke-Native {
            git -C $mainPath merge --ff-only $Target
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

Write-Host "`n=== WO-005 CLOSURE PREFLIGHT ==="

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
    if ($identity -ne $publishedMain) {
        throw "Main identity differs from the published WO-005 verdict commit."
    }
}

Assert-AllWorktreesClean `
    -Repository $repo `
    -Label "Preflight"

$publishedCommitCount = [int](
    git -C $repo rev-list `
        --count `
        "$preIntegrationMain..$publishedMain"
).Trim()

if ($publishedCommitCount -ne 5) {
    throw "The published WO-005 sequence does not contain exactly five commits."
}

$publishedMergeCount = @(
    git -C $repo rev-list `
        --merges `
        "$preIntegrationMain..$publishedMain"
).Count

if ($publishedMergeCount -ne 0) {
    throw "The published WO-005 sequence contains merge commits."
}

$actualPublishedPaths = @(
    git -C $repo diff `
        --name-only `
        $preIntegrationMain `
        $publishedMain
)

Assert-ExactPathSet `
    -Actual $actualPublishedPaths `
    -Expected $publishedPaths `
    -Label "Published WO-005 sequence"

$forbiddenPublishedChanges = @(
    git -C $repo diff `
        --name-only `
        $preIntegrationMain `
        $publishedMain `
        -- `
        aegis_os `
        tests `
        pyproject.toml `
        .github
)

if ($forbiddenPublishedChanges.Count -ne 0) {
    throw "Published WO-005 includes forbidden runtime, test, dependency, or CI changes."
}

if (Test-Path -LiteralPath $closureWorktree) {
    throw "WO-005 closure worktree already exists: $closureWorktree"
}

if (@(git -C $repo branch --list $closureBranch).Count -ne 0) {
    throw "WO-005 closure branch already exists: $closureBranch"
}

$remoteSnapshotBefore = Get-RemoteSnapshot $repo
$remoteNonMainBefore = Get-NonMainRemoteSnapshot $remoteSnapshotBefore

$publishedTree = (
    git -C $repo rev-parse "${publishedMain}^{tree}"
).Trim()

Write-Host "Published sequence, exact six-path boundary, remote identity, and clean-state: PASS"

Write-Host "`n=== CREATE WO-005 CLOSURE WORKTREE ==="

Invoke-Native {
    git -C $repo worktree add `
        -b $closureBranch `
        $closureWorktree `
        $publishedMain
} "WO-005 closure worktree creation" | Out-Null

$workOrderPath = Join-Path $closureWorktree $workOrderRelative
$traceabilityPath = Join-Path $closureWorktree $traceabilityRelative

try {
    Write-Host "`n=== RECORD WO-005 CLOSURE ==="

    $workOrder = [System.IO.File]::ReadAllText($workOrderPath)
    $workOrder = $workOrder -replace "`r`n", "`n"

    $traceability = [System.IO.File]::ReadAllText($traceabilityPath)
    $traceability = $traceability -replace "`r`n", "`n"

    if ($workOrder.Contains("## WO-005 closure record")) {
        throw "WO-005 closure record already exists."
    }

    if ($traceability.Contains("## TR-013 WO-005 Closure")) {
        throw "TR-013 WO-005 closure already exists."
    }

    $workOrder = Replace-ExactlyOnce `
        -Text $workOrder `
        -OldValue "**Status:** ACTIVE - ACCEPTED-DESIGN CANDIDATE REVIEW PASSED" `
        -NewValue "**Status:** CLOSED - ACCEPTED DESIGN PUBLISHED" `
        -Label "WO-005 status"

    $oldDisposition = @"
WO-005: ACTIVE - ACCEPTED-DESIGN CANDIDATE REVIEW PASSED
Authoritative base: $architecturalBase
Governance amendment main: $preIntegrationMain
Specification at base: PRE-EXISTING - PROPOSED
Deliverable scope: FOUR EXISTING DOCUMENTATION PATHS
Deliverable candidate designated: f2376dce1bd4e312ca80a53aff9ab6212bb19289
Candidate tree: 2b18f80f57e7b690e1773f67d20112d6dee10633
Architecture review: PASS
QA review: PASS
Candidate review verdict: PASS
Deliverable integration authority: NOT GRANTED
Deliverable publication authority: NOT GRANTED
Runtime implementation authority: NOT GRANTED
"@

    $newDisposition = @"
WO-005: CLOSED - ACCEPTED DESIGN PUBLISHED
Authoritative base: $architecturalBase
Governance amendment main: $preIntegrationMain
Specification at base: PRE-EXISTING - PROPOSED
Deliverable scope: FOUR EXISTING DOCUMENTATION PATHS
Deliverable candidate designated: f2376dce1bd4e312ca80a53aff9ab6212bb19289
Candidate tree: 2b18f80f57e7b690e1773f67d20112d6dee10633
Architecture review: PASS
QA review: PASS
Candidate review verdict: PASS
Deliverable integration: COMPLETE
Deliverable publication: COMPLETE
Published main: $publishedMain
Published tree: $publishedTree
Closure status: RECORDED BY THIS GOVERNANCE COMMIT
Runtime implementation authority: NOT GRANTED
"@

    $workOrder = Replace-ExactlyOnce `
        -Text $workOrder `
        -OldValue $oldDisposition.TrimEnd() `
        -NewValue $newDisposition.TrimEnd() `
        -Label "WO-005 current disposition"

    $closureSection = @"

## WO-005 closure record

- Closure date: 2026-07-31
- Product Owner / Founder closure authorization: explicit
- Authoritative architectural base: ``$architecturalBase``
- Pre-integration governance main: ``$preIntegrationMain``
- Published reviewed main: ``$publishedMain``
- Published reviewed tree: ``$publishedTree``
- Published commit count: 5
- Published changed-path count: 6
- Publication type: strict fast-forward
- Force push: no
- Merge commits: 0
- Runtime changes: 0
- Test changes: 0
- Dependency changes: 0
- CI changes: 0
- Tag created: no
- Release created: no
- Ruleset changed: no
- Worktree cleanup performed: no
- Runtime implementation authority: not granted

### Published linear sequence

1. ``$technicalIntegrated`` — Accept WO-005 environment interaction design
2. ``$designationIntegrated`` — Designate WO-005 accepted design candidate
3. ``$architectureReviewIntegrated`` — Record WO-005 architecture review
4. ``$qaReviewIntegrated`` — Record WO-005 QA review
5. ``$finalVerdictIntegrated`` — Record WO-005 candidate review verdict

### Final disposition

WO-005 is closed because the amended, reviewed, documentation-only Environment
Interaction Layer design was integrated and published to ``main`` with exact
technical and governance content identity.

ADR-006, the architecture, the pre-existing implementation specification, and
the roadmap now record the accepted simulation-first design. The current
runtime remains unchanged.

This closure grants no authority to implement the environment runtime, modify
tests, integrate the design into execution, access providers, perform external
I/O, create credentials, tags, or releases, change rulesets, or clean up
preserved branches and worktrees.

Any runtime implementation requires a new, separately authorized work order
based on the accepted specification.
"@

    $workOrder = $workOrder.TrimEnd() + $closureSection + "`n"

    $traceabilitySection = @"

## TR-013 WO-005 Closure

- Work order: WO-005 - Environment Interaction Layer Architecture Acceptance and Implementation Specification
- Closure date: 2026-07-31
- Authoritative architectural base: ``$architecturalBase``
- Pre-integration governance main: ``$preIntegrationMain``
- Published reviewed main: ``$publishedMain``
- Published reviewed tree: ``$publishedTree``
- Published sequence length: 5 commits
- Published path boundary: exactly six technical and governance documents
- Architecture review: pass
- QA review: pass
- Candidate verdict: pass
- Strict fast-forward publication: pass
- Runtime, test, dependency, and CI changes: none
- Force push: no
- Merge commits: none
- Tag, release, and ruleset changes: none
- Worktree cleanup: not performed
- Final work-order state: **CLOSED - ACCEPTED DESIGN PUBLISHED**
- Runtime implementation authority: not granted

The exact reviewed design and governance records were published as a linear
five-commit fast-forward from the amended governance main. This closure records
the completed documentation state only and grants no runtime, provider,
integration, release, ruleset, or cleanup authority.
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

    Write-Host "WO-005 closure work order and traceability: WRITTEN"

    Write-Host "`n=== VALIDATE CLOSURE BOUNDARY ==="

    $changedPaths = @(
        git -C $closureWorktree status --short |
            ForEach-Object { $_.Substring(3) }
    )

    Assert-ExactPathSet `
        -Actual $changedPaths `
        -Expected $closurePaths `
        -Label "WO-005 closure"

    Invoke-Native {
        git -C $closureWorktree diff --check
    } "WO-005 closure whitespace validation" | Out-Null

    $forbiddenClosureChanges = @(
        git -C $closureWorktree diff `
            --name-only `
            $publishedMain `
            -- `
            docs `
            aegis_os `
            tests `
            pyproject.toml `
            .github
    )

    if ($forbiddenClosureChanges.Count -ne 0) {
        throw "WO-005 closure changed technical, runtime, test, dependency, or CI paths."
    }

    $finalWorkOrder = [System.IO.File]::ReadAllText($workOrderPath)
    $finalTraceability = [System.IO.File]::ReadAllText($traceabilityPath)

    foreach ($requiredText in @(
        "**Status:** CLOSED - ACCEPTED DESIGN PUBLISHED",
        "## WO-005 closure record",
        "Deliverable integration: COMPLETE",
        "Deliverable publication: COMPLETE",
        "Runtime implementation authority: NOT GRANTED",
        "Any runtime implementation requires a new, separately authorized work order"
    )) {
        if (-not $finalWorkOrder.Contains($requiredText)) {
            throw "Required WO-005 closure text is missing: $requiredText"
        }
    }

    foreach ($requiredText in @(
        "## TR-013 WO-005 Closure",
        "Final work-order state: **CLOSED - ACCEPTED DESIGN PUBLISHED**",
        "Runtime implementation authority: not granted"
    )) {
        if (-not $finalTraceability.Contains($requiredText)) {
            throw "Required traceability closure text is missing: $requiredText"
        }
    }

    Write-Host "Exact two-path closure boundary and zero technical changes: PASS"
    Write-Host "Git LF/CRLF conversion warnings: NON-BLOCKING"

    Write-Host "`n=== COMMIT WO-005 CLOSURE ==="

    Invoke-Native {
        git -C $closureWorktree add -- $closurePaths
    } "WO-005 closure staging" | Out-Null

    $stagedPaths = @(
        git -C $closureWorktree diff --cached --name-only
    )

    Assert-ExactPathSet `
        -Actual $stagedPaths `
        -Expected $closurePaths `
        -Label "Staged WO-005 closure"

    Invoke-Native {
        git -C $closureWorktree diff --cached --check
    } "Staged WO-005 closure validation" | Out-Null

    Invoke-Native {
        git -C $closureWorktree commit -m $closureSubject
    } "WO-005 closure commit creation" | Out-Null

    $closureCommit = (
        git -C $closureWorktree rev-parse HEAD
    ).Trim()

    $closureParent = (
        git -C $closureWorktree rev-parse HEAD^
    ).Trim()

    $closureTree = (
        git -C $closureWorktree rev-parse "HEAD^{tree}"
    ).Trim()

    $actualClosureSubject = (
        git -C $closureWorktree log -1 --format=%s
    ).Trim()

    if ($closureParent -ne $publishedMain) {
        throw "WO-005 closure parent mismatch."
    }

    if ($actualClosureSubject -ne $closureSubject) {
        throw "WO-005 closure subject mismatch."
    }

    $committedPaths = @(
        git -C $closureWorktree diff-tree `
            --no-commit-id `
            --name-only `
            -r `
            HEAD
    )

    Assert-ExactPathSet `
        -Actual $committedPaths `
        -Expected $closurePaths `
        -Label "Committed WO-005 closure"

    if (@(git -C $closureWorktree status --short).Count -ne 0) {
        throw "WO-005 closure worktree is not clean after commit."
    }

    Write-Host "WO-005 governance-only closure commit: CREATED"

    Write-Host "`n=== STRICT FAST-FORWARD CLOSURE PUBLICATION ==="

    Invoke-Native {
        git -C $repo fetch origin `
            "+refs/heads/main:refs/remotes/origin/main"
    } "Pre-closure-publication remote refresh" | Out-Null

    $originImmediatelyBefore = (
        git -C $repo rev-parse refs/remotes/origin/main
    ).Trim()

    $liveImmediatelyBefore = Get-LiveRemoteMain $repo

    if (
        $originImmediatelyBefore -ne $publishedMain -or
        $liveImmediatelyBefore -ne $publishedMain
    ) {
        throw "Remote main changed before WO-005 closure publication."
    }

    Invoke-Native {
        git -C $closureWorktree merge-base `
            --is-ancestor `
            $publishedMain `
            $closureCommit
    } "Closure fast-forward ancestry validation" | Out-Null

    Assert-AllWorktreesClean `
        -Repository $repo `
        -Label "Pre-closure-publication"

    $pushOutput = @(
        Invoke-Native {
            git -C $closureWorktree push `
                --porcelain `
                origin `
                "${closureCommit}:refs/heads/main"
        } "WO-005 closure fast-forward push"
    )

    $pushOutput | ForEach-Object { Write-Host $_ }

    Write-Host "WO-005 closure fast-forward push: COMPLETE"

    Write-Host "`n=== VERIFY AND SYNCHRONIZE FINAL MAIN ==="

    Invoke-Native {
        git -C $repo fetch origin `
            "+refs/heads/main:refs/remotes/origin/main"
    } "Post-closure-publication remote refresh" | Out-Null

    $liveAfter = Get-LiveRemoteMain $repo

    $originAfter = (
        git -C $repo rev-parse refs/remotes/origin/main
    ).Trim()

    if ($liveAfter -ne $closureCommit) {
        throw "Live remote main does not match the WO-005 closure commit."
    }

    if ($originAfter -ne $closureCommit) {
        throw "origin/main does not match the WO-005 closure commit."
    }

    Move-LocalMainFastForward `
        -Repository $repo `
        -ExpectedOld $publishedMain `
        -Target $closureCommit

    $localMainAfter = (
        git -C $repo rev-parse refs/heads/main
    ).Trim()

    if ($localMainAfter -ne $closureCommit) {
        throw "Local main does not match the WO-005 closure commit."
    }

    $remoteSnapshotAfter = Get-RemoteSnapshot $repo
    $remoteNonMainAfter = Get-NonMainRemoteSnapshot $remoteSnapshotAfter

    Assert-SequenceEqual `
        -Before $remoteNonMainBefore `
        -After $remoteNonMainAfter `
        -Label "Non-main remote heads and tags"

    Assert-AllWorktreesClean `
        -Repository $repo `
        -Label "Final"

    $finalClosureDelta = @(
        git -C $repo diff `
            --name-only `
            $publishedMain `
            $closureCommit
    )

    Assert-ExactPathSet `
        -Actual $finalClosureDelta `
        -Expected $closurePaths `
        -Label "Published WO-005 closure"

    $publishedClosureCommitCount = [int](
        git -C $repo rev-list `
            --count `
            "$publishedMain..$closureCommit"
    ).Trim()

    if ($publishedClosureCommitCount -ne 1) {
        throw "Expected exactly one published closure commit."
    }

    Write-Host "Remote, origin/main, local main, non-main refs, and closure boundary: PASS"

    Write-Host "`n=== WRITE WO-005 CLOSURE MANIFEST ==="

    New-Item `
        -ItemType Directory `
        -Path $logDirectory `
        -Force | Out-Null

    $manifest = @"
AEGIS WO-005 Closure
====================

Date: 2026-07-31

Published reviewed main before closure:
$publishedMain

Published reviewed tree:
$publishedTree

Closure commit:
$closureCommit

Closure parent:
$closureParent

Closure tree:
$closureTree

Closure subject:
$actualClosureSubject

Closure changed paths:
$($committedPaths -join "`r`n")

Final main:
$liveAfter

Validation:
- Reviewed publication sequence length: 5
- Reviewed publication merge commits: 0
- Reviewed publication changed paths: 6
- Closure commit count: 1
- Closure changed paths: 2
- Technical-document changes in closure: 0
- Runtime changes in closure: 0
- Test changes in closure: 0
- Dependency changes in closure: 0
- CI changes in closure: 0
- Strict fast-forward publication: PASS
- Force push: NO
- Non-main remote heads changed: NO
- Remote tags changed: NO
- Tag created: NO
- Release created: NO
- Ruleset changed: NO
- Worktree cleanup performed: NO
- Worktrees clean: PASS
- origin/main synchronized: PASS
- Local main synchronized: PASS
- Runtime implementation authority: NO
- Final work-order state: CLOSED - ACCEPTED DESIGN PUBLISHED
"@

    [System.IO.File]::WriteAllText(
        $manifestPath,
        $manifest,
        $utf8NoBom
    )

    Write-Host "`n=== WO-005 CLOSURE RESULT ==="

    [pscustomobject]@{
        ArchitecturalBase = $architecturalBase
        PreIntegrationMain = $preIntegrationMain
        PublishedReviewedMain = $publishedMain
        PublishedReviewedTree = $publishedTree
        ReviewedSequenceCommitCount = $publishedCommitCount
        ReviewedSequenceChangedPathCount = $actualPublishedPaths.Count
        ClosureCommit = $closureCommit
        ClosureParent = $closureParent
        ClosureTree = $closureTree
        ClosureSubject = $actualClosureSubject
        ClosurePathCount = $committedPaths.Count
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
        NonMainRemoteRefsChanged = $false
        RemoteTagsChanged = $false
        TagCreated = $false
        ReleaseCreated = $false
        RulesetChanged = $false
        WorktreeCleanupPerformed = $false
        WorktreesClean = $true
        Manifest = $manifestPath
        RuntimeImplementationAuthorized = $false
        FinalStatus = "WO-005 CLOSED - ACCEPTED DESIGN PUBLISHED"
    } | Format-List

    Write-Host "Closure paths:"
    $committedPaths | ForEach-Object { Write-Host " - $_" }

    Write-Host "`nWO-005 CLOSURE: COMPLETE"
    Write-Host "WO-005 is closed with the accepted Environment Interaction Layer design published on main."
    Write-Host "Remote main, origin/main, and local main now equal $closureCommit."
    Write-Host "No runtime implementation, force push, tag, release, ruleset change, or worktree cleanup was performed."
}
catch {
    if (Test-Path -LiteralPath $closureWorktree) {
        Write-Host "`nWO-005 closure worktree preserved for diagnosis:"
        git -C $closureWorktree status --short
    }

    throw
}
