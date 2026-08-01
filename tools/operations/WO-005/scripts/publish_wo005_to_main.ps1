$ErrorActionPreference = "Stop"

if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$repo = "$env:USERPROFILE\Projects\aegis-platform"
$mainWorktree = "$env:USERPROFILE\Projects\aegis-platform-wo-005-local-integration"

$expectedRemoteMain = "ad743b4568bbd82527f7ff192c5b10ca4d59c2e9"
$expectedLocalMain = "7463aa6701a2246d9035476c7355007cb7051574"

$technicalSource = "f2376dce1bd4e312ca80a53aff9ab6212bb19289"
$finalVerdictSource = "719b44008640a2899e19218f628056cfe3022e76"

$expectedSubjects = @(
    "Accept WO-005 environment interaction design",
    "Designate WO-005 accepted design candidate",
    "Record WO-005 architecture review",
    "Record WO-005 QA review",
    "Record WO-005 candidate review verdict"
)

$deliverablePaths = @(
    "docs/adr/ADR-006-environment-interaction-layer.md",
    "docs/architecture/environment-interaction-layer.md",
    "docs/roadmap/ROADMAP.md",
    "docs/specifications/v0.5-phase-b-environment-interaction-layer.md"
)

$governancePaths = @(
    "governance/TRACEABILITY.md",
    "governance/work-orders/WO-005_ENVIRONMENT_INTERACTION_LAYER_SPECIFICATION.md"
)

$expectedFinalPaths = @(
    $deliverablePaths + $governancePaths
)

$operationsRoot = [Environment]::GetEnvironmentVariable(
    "AEGIS_OPERATIONS",
    "User"
)

if ([string]::IsNullOrWhiteSpace($operationsRoot)) {
    $operationsRoot = "$env:USERPROFILE\Projects\AEGIS-operations"
}

$logDirectory = Join-Path $operationsRoot "logs\WO-005"
$manifestPath = Join-Path $logDirectory "WO-005-remote-publication.txt"
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

function Get-RemoteRefSnapshot {
    param([string]$Repository)

    return @(
        Invoke-Native {
            git -C $Repository ls-remote --heads --tags origin
        } "Remote heads and tags snapshot" |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_ } |
            Sort-Object
    )
}

function Get-RemoteSnapshotWithoutMain {
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

    for ($i = 0; $i -lt $Before.Count; $i++) {
        if ($Before[$i] -ne $After[$i]) {
            Write-Host "$Label first mismatch:"
            Write-Host "Before: $($Before[$i])"
            Write-Host "After : $($After[$i])"
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

function Assert-BlobIdentity {
    param(
        [string]$Repository,
        [string]$SourceCommit,
        [string]$PublishedCommit,
        [string[]]$Paths,
        [string]$Label
    )

    foreach ($path in $Paths) {
        $sourceBlob = (
            git -C $Repository rev-parse "${SourceCommit}:$path"
        ).Trim()

        $publishedBlob = (
            git -C $Repository rev-parse "${PublishedCommit}:$path"
        ).Trim()

        if ($sourceBlob -ne $publishedBlob) {
            throw "$Label blob mismatch: $path"
        }
    }
}

Write-Host "`n=== WO-005 REMOTE PUBLICATION PREFLIGHT ==="

if (-not (Test-Path -LiteralPath $repo)) {
    throw "Repository not found: $repo"
}

if (-not (Test-Path -LiteralPath $mainWorktree)) {
    throw "Local main integration worktree not found: $mainWorktree"
}

Invoke-Native {
    git -C $repo fetch origin `
        "+refs/heads/main:refs/remotes/origin/main"
} "Remote main refresh" | Out-Null

$localMainBefore = (
    git -C $repo rev-parse refs/heads/main
).Trim()

$integrationHead = (
    git -C $mainWorktree rev-parse HEAD
).Trim()

$integrationBranch = (
    git -C $mainWorktree symbolic-ref --short HEAD
).Trim()

$originMainBefore = (
    git -C $repo rev-parse refs/remotes/origin/main
).Trim()

$liveMainBefore = Get-LiveRemoteMain $repo

if ($localMainBefore -ne $expectedLocalMain) {
    throw "Local main differs from the authorized WO-005 integration commit."
}

if ($integrationHead -ne $expectedLocalMain) {
    throw "Integration worktree HEAD differs from the authorized WO-005 integration commit."
}

if ($integrationBranch -ne "main") {
    throw "Integration worktree is not on main."
}

if (
    $originMainBefore -ne $expectedRemoteMain -or
    $liveMainBefore -ne $expectedRemoteMain
) {
    throw "Remote main differs from the authorized pre-publication commit."
}

Assert-AllWorktreesClean `
    -Repository $repo `
    -Label "Preflight"

Invoke-Native {
    git -C $repo merge-base `
        --is-ancestor `
        $expectedRemoteMain `
        $expectedLocalMain
} "Strict fast-forward ancestry validation" | Out-Null

$commitCount = [int](
    git -C $repo rev-list `
        --count `
        "$expectedRemoteMain..$expectedLocalMain"
).Trim()

if ($commitCount -ne 5) {
    throw "Expected exactly five commits for publication, found $commitCount."
}

$mergeCommitCount = @(
    git -C $repo rev-list `
        --merges `
        "$expectedRemoteMain..$expectedLocalMain"
).Count

if ($mergeCommitCount -ne 0) {
    throw "The publication sequence contains merge commits."
}

$subjects = @(
    git -C $repo log `
        --reverse `
        --format=%s `
        "$expectedRemoteMain..$expectedLocalMain"
)

Assert-SequenceEqual `
    -Before $expectedSubjects `
    -After $subjects `
    -Label "WO-005 publication subject sequence"

$changedPaths = @(
    git -C $repo diff `
        --name-only `
        $expectedRemoteMain `
        $expectedLocalMain
)

Assert-ExactPathSet `
    -Actual $changedPaths `
    -Expected $expectedFinalPaths `
    -Label "WO-005 publication"

Invoke-Native {
    git -C $repo diff `
        --check `
        $expectedRemoteMain `
        $expectedLocalMain
} "Publication whitespace validation" | Out-Null

$forbiddenChanges = @(
    git -C $repo diff `
        --name-only `
        $expectedRemoteMain `
        $expectedLocalMain `
        -- `
        aegis_os `
        tests `
        pyproject.toml `
        .github
)

if ($forbiddenChanges.Count -ne 0) {
    throw "Publication contains forbidden runtime, test, dependency, or CI changes."
}

Assert-BlobIdentity `
    -Repository $repo `
    -SourceCommit $technicalSource `
    -PublishedCommit $expectedLocalMain `
    -Paths $deliverablePaths `
    -Label "Reviewed technical content"

Assert-BlobIdentity `
    -Repository $repo `
    -SourceCommit $finalVerdictSource `
    -PublishedCommit $expectedLocalMain `
    -Paths $governancePaths `
    -Label "Reviewed governance content"

$remoteSnapshotBefore = Get-RemoteRefSnapshot $repo
$remoteNonMainBefore = Get-RemoteSnapshotWithoutMain $remoteSnapshotBefore

Write-Host "Local integration, remote lease, sequence, paths, blobs, and clean-state: PASS"

Write-Host "`n=== STRICT FAST-FORWARD PUBLICATION ==="

$pushOutput = @(
    Invoke-Native {
        git -C $mainWorktree push `
            --porcelain `
            origin `
            "${expectedLocalMain}:refs/heads/main"
    } "WO-005 strict fast-forward publication"
)

$pushOutput | ForEach-Object { Write-Host $_ }

Write-Host "WO-005 main publication push: COMPLETE"

Write-Host "`n=== VERIFY PUBLISHED STATE ==="

Invoke-Native {
    git -C $repo fetch origin `
        "+refs/heads/main:refs/remotes/origin/main"
} "Post-publication remote refresh" | Out-Null

$liveMainAfter = Get-LiveRemoteMain $repo

$originMainAfter = (
    git -C $repo rev-parse refs/remotes/origin/main
).Trim()

$localMainAfter = (
    git -C $repo rev-parse refs/heads/main
).Trim()

$integrationHeadAfter = (
    git -C $mainWorktree rev-parse HEAD
).Trim()

foreach ($identity in @(
    $liveMainAfter,
    $originMainAfter,
    $localMainAfter,
    $integrationHeadAfter
)) {
    if ($identity -ne $expectedLocalMain) {
        throw "Published main identity mismatch."
    }
}

$remoteSnapshotAfter = Get-RemoteRefSnapshot $repo
$remoteNonMainAfter = Get-RemoteSnapshotWithoutMain $remoteSnapshotAfter

Assert-SequenceEqual `
    -Before $remoteNonMainBefore `
    -After $remoteNonMainAfter `
    -Label "Non-main remote heads and tags"

Assert-AllWorktreesClean `
    -Repository $repo `
    -Label "Post-publication"

$publishedTree = (
    git -C $repo rev-parse "${expectedLocalMain}^{tree}"
).Trim()

$publishedCommitCount = [int](
    git -C $repo rev-list `
        --count `
        "$expectedRemoteMain..$liveMainAfter"
).Trim()

if ($publishedCommitCount -ne 5) {
    throw "Published remote sequence does not contain exactly five commits."
}

$publishedMergeCount = @(
    git -C $repo rev-list `
        --merges `
        "$expectedRemoteMain..$liveMainAfter"
).Count

if ($publishedMergeCount -ne 0) {
    throw "Published remote sequence contains merge commits."
}

$publishedChangedPaths = @(
    git -C $repo diff `
        --name-only `
        $expectedRemoteMain `
        $liveMainAfter
)

Assert-ExactPathSet `
    -Actual $publishedChangedPaths `
    -Expected $expectedFinalPaths `
    -Label "Published WO-005 state"

Write-Host "Remote main, origin/main, local main, remote refs, and five-commit sequence: PASS"

Write-Host "`n=== WRITE PUBLICATION MANIFEST ==="

New-Item `
    -ItemType Directory `
    -Path $logDirectory `
    -Force | Out-Null

$manifest = @"
AEGIS WO-005 Remote Publication
===============================

Date: 2026-07-31

Previous remote main:
$expectedRemoteMain

Published main:
$liveMainAfter

Published tree:
$publishedTree

Publication type:
STRICT FAST-FORWARD

Published sequence:
$($subjects -join "`r`n")

Published paths:
$($publishedChangedPaths -join "`r`n")

Validation:
- Commit count: $publishedCommitCount
- Merge commits: $publishedMergeCount
- Exact changed path count: $($publishedChangedPaths.Count)
- Technical blobs equal reviewed candidate: PASS
- Governance blobs equal reviewed verdict: PASS
- Runtime changes: 0
- Test changes: 0
- Dependency changes: 0
- CI changes: 0
- Force push: NO
- Non-main remote heads changed: NO
- Remote tags changed: NO
- Tag created: NO
- Release created: NO
- Ruleset change performed: NO
- Worktree cleanup performed: NO
- Worktrees clean: PASS
- origin/main synchronized: PASS
- Local main synchronized: PASS
- Runtime implementation authorized: NO
"@

[System.IO.File]::WriteAllText(
    $manifestPath,
    $manifest,
    $utf8NoBom
)

Write-Host "`n=== WO-005 REMOTE PUBLICATION RESULT ==="

[pscustomobject]@{
    PreviousRemoteMain = $expectedRemoteMain
    PublishedMain = $liveMainAfter
    PublishedTree = $publishedTree
    PublishedCommitCount = $publishedCommitCount
    PublishedChangedPathCount = $publishedChangedPaths.Count
    PushType = "STRICT FAST-FORWARD"
    ForcePush = $false
    MergeCommits = $publishedMergeCount
    TechnicalBlobIdentity = "PASS"
    GovernanceBlobIdentity = "PASS"
    RuntimeChanges = 0
    TestChanges = 0
    DependencyChanges = 0
    CIChanges = 0
    NonMainRemoteRefsChanged = $false
    RemoteTagsChanged = $false
    OriginMain = $originMainAfter
    LocalMain = $localMainAfter
    MainWorktreeHead = $integrationHeadAfter
    WorktreesClean = $true
    TagCreated = $false
    ReleaseCreated = $false
    RulesetChanged = $false
    WorktreeCleanupPerformed = $false
    Manifest = $manifestPath
    RuntimeImplementationAuthorized = $false
    FinalStatus = "WO-005 PUBLISHED TO MAIN - CLOSURE NOT YET AUTHORIZED"
} | Format-List

Write-Host "Published paths:"
$publishedChangedPaths | ForEach-Object { Write-Host " - $_" }

Write-Host "`nWO-005 REMOTE PUBLICATION: COMPLETE"
Write-Host "Remote main, origin/main, and local main now equal $liveMainAfter."
Write-Host "The reviewed five-commit WO-005 sequence was published by strict fast-forward."
Write-Host "No force push, runtime implementation, tag, release, ruleset change, or worktree cleanup was performed."
