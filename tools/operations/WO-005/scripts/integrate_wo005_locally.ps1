$ErrorActionPreference = "Stop"

if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$repo = "$env:USERPROFILE\Projects\aegis-platform"
$integrationWorktreeFallback = "$env:USERPROFILE\Projects\aegis-platform-wo-005-local-integration"

$architecturalBase = "be7502f73b51808d54728f912ead46ad0073c7b9"
$governanceMain = "ad743b4568bbd82527f7ff192c5b10ca4d59c2e9"

$candidateCommit = "f2376dce1bd4e312ca80a53aff9ab6212bb19289"
$designationCommit = "9fa4f7779ec3a772db3fce7f6d2e6138659df92f"
$architectureReviewCommit = "12432c2a334998fd54a8dd298b9afc14bbd4b650"
$qaReviewCommit = "100b7d21a01eccb28955c3811b043f8a62e75e2b"
$finalVerdictCommit = "719b44008640a2899e19218f628056cfe3022e76"

$candidateBranch = "documentation/wo-005-accepted-environment-interaction-design-local-fix"
$designationBranch = "governance/wo-005-accepted-candidate-designation-local-fix"
$reviewSourceBranch = "governance/wo-005-review-verdict"

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

$finalExpectedPaths = @(
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
$manifestPath = Join-Path $logDirectory "WO-005-local-integration.txt"
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

function Assert-OneParent {
    param(
        [string]$Repository,
        [string]$Commit,
        [string]$Label
    )

    $line = (
        git -C $Repository rev-list --parents -n 1 $Commit
    ).Trim()

    $parts = @($line -split "\s+")

    if ($parts.Count -ne 2) {
        throw "$Label is not a single-parent commit."
    }

    return $parts[1]
}

function Assert-SourceCommit {
    param(
        [string]$Repository,
        [string]$Commit,
        [string]$ExpectedParent,
        [string[]]$ExpectedPaths,
        [string]$Label
    )

    $parent = Assert-OneParent `
        -Repository $Repository `
        -Commit $Commit `
        -Label $Label

    if ($parent -ne $ExpectedParent) {
        throw "$Label parent mismatch."
    }

    $paths = @(
        git -C $Repository diff-tree `
            --no-commit-id `
            --name-only `
            -r `
            $Commit
    )

    Assert-ExactPathSet `
        -Actual $paths `
        -Expected $ExpectedPaths `
        -Label $Label
}

function Assert-BlobIdentity {
    param(
        [string]$Repository,
        [string]$SourceCommit,
        [string]$IntegratedCommit,
        [string[]]$Paths,
        [string]$Label
    )

    foreach ($path in $Paths) {
        $sourceBlob = (
            git -C $Repository rev-parse "${SourceCommit}:$path"
        ).Trim()

        $integratedBlob = (
            git -C $Repository rev-parse "${IntegratedCommit}:$path"
        ).Trim()

        if ($sourceBlob -ne $integratedBlob) {
            throw "$Label blob mismatch: $path"
        }
    }
}

function Apply-SourceCommit {
    param(
        [string]$Worktree,
        [string]$SourceCommit,
        [string]$ExpectedCurrentHead,
        [string[]]$ExpectedPaths,
        [string]$Label
    )

    $before = (
        git -C $Worktree rev-parse HEAD
    ).Trim()

    if ($before -ne $ExpectedCurrentHead) {
        throw "$Label expected HEAD $ExpectedCurrentHead but found $before."
    }

    $sourceSubject = (
        git -C $Worktree log -1 --format=%s $SourceCommit
    ).Trim()

    Invoke-Native {
        git -C $Worktree cherry-pick $SourceCommit
    } "$Label cherry-pick"

    $integratedCommit = (
        git -C $Worktree rev-parse HEAD
    ).Trim()

    $integratedParent = Assert-OneParent `
        -Repository $Worktree `
        -Commit $integratedCommit `
        -Label "$Label integrated commit"

    if ($integratedParent -ne $before) {
        throw "$Label integrated parent mismatch."
    }

    $integratedSubject = (
        git -C $Worktree log -1 --format=%s $integratedCommit
    ).Trim()

    if ($integratedSubject -ne $sourceSubject) {
        throw "$Label subject mismatch after integration."
    }

    $integratedPaths = @(
        git -C $Worktree diff-tree `
            --no-commit-id `
            --name-only `
            -r `
            $integratedCommit
    )

    Assert-ExactPathSet `
        -Actual $integratedPaths `
        -Expected $ExpectedPaths `
        -Label "$Label integrated commit"

    Invoke-Native {
        git -C $Worktree diff-tree `
            --check `
            $integratedParent `
            $integratedCommit
    } "$Label whitespace validation"

    Assert-BlobIdentity `
        -Repository $Worktree `
        -SourceCommit $SourceCommit `
        -IntegratedCommit $integratedCommit `
        -Paths $ExpectedPaths `
        -Label $Label

    if (@(git -C $Worktree status --short).Count -ne 0) {
        throw "$Label left the main worktree dirty."
    }

    return [pscustomobject]@{
        Source = $SourceCommit
        Integrated = $integratedCommit
        Parent = $integratedParent
        Subject = $integratedSubject
        PathCount = $integratedPaths.Count
    }
}

function Restore-LocalMain {
    param(
        [string]$Worktree,
        [string]$Target
    )

    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    try {
        git -C $Worktree cherry-pick --abort 2>$null | Out-Null
        git -C $Worktree reset --hard $Target
        $resetExit = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedPreference
    }

    if ($resetExit -ne 0) {
        Write-Host "WARNING: automatic local-main restoration failed."
        return $false
    }

    return (
        (git -C $Worktree rev-parse HEAD).Trim() -eq $Target -and
        @(git -C $Worktree status --short).Count -eq 0
    )
}

Write-Host "`n=== WO-005 LOCAL INTEGRATION PREFLIGHT ==="

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
        throw "Main identity differs from the reviewed WO-005 governance base."
    }
}

Assert-AllWorktreesClean `
    -Repository $repo `
    -Label "Preflight"

if (
    (git -C $repo rev-parse "refs/heads/$candidateBranch").Trim() -ne
    $candidateCommit
) {
    throw "Candidate branch identity mismatch."
}

if (
    (git -C $repo rev-parse "refs/heads/$designationBranch").Trim() -ne
    $designationCommit
) {
    throw "Designation branch identity mismatch."
}

if (
    (git -C $repo rev-parse "refs/heads/$reviewSourceBranch").Trim() -ne
    $finalVerdictCommit
) {
    throw "Review verdict branch identity mismatch."
}

Assert-SourceCommit `
    -Repository $repo `
    -Commit $candidateCommit `
    -ExpectedParent $architecturalBase `
    -ExpectedPaths $deliverablePaths `
    -Label "WO-005 technical candidate"

Assert-SourceCommit `
    -Repository $repo `
    -Commit $designationCommit `
    -ExpectedParent $governanceMain `
    -ExpectedPaths $governancePaths `
    -Label "WO-005 candidate designation"

Assert-SourceCommit `
    -Repository $repo `
    -Commit $architectureReviewCommit `
    -ExpectedParent $designationCommit `
    -ExpectedPaths $governancePaths `
    -Label "WO-005 architecture review"

Assert-SourceCommit `
    -Repository $repo `
    -Commit $qaReviewCommit `
    -ExpectedParent $architectureReviewCommit `
    -ExpectedPaths $governancePaths `
    -Label "WO-005 QA review"

Assert-SourceCommit `
    -Repository $repo `
    -Commit $finalVerdictCommit `
    -ExpectedParent $qaReviewCommit `
    -ExpectedPaths $governancePaths `
    -Label "WO-005 final review verdict"

Write-Host "Source commits, exact parents, exact paths, main, and remote identities: PASS"

Write-Host "`n=== RESOLVE LOCAL MAIN WORKTREE ==="

$mainWorktrees = @(
    Get-RegisteredWorktrees $repo |
        Where-Object { $_.Branch -eq "refs/heads/main" }
)

if ($mainWorktrees.Count -gt 1) {
    throw "Main is checked out in more than one worktree."
}

if ($mainWorktrees.Count -eq 1) {
    $mainWorktree = $mainWorktrees[0].Path
    Write-Host "Existing main worktree:" $mainWorktree
}
else {
    if (Test-Path -LiteralPath $integrationWorktreeFallback) {
        throw "Fallback integration worktree path already exists: $integrationWorktreeFallback"
    }

    Invoke-Native {
        git -C $repo worktree add `
            $integrationWorktreeFallback `
            main
    } "Local main integration worktree creation"

    $mainWorktree = $integrationWorktreeFallback
    Write-Host "Created main integration worktree:" $mainWorktree
}

if (@(git -C $mainWorktree status --short).Count -ne 0) {
    throw "The local main worktree is not clean."
}

if (
    (git -C $mainWorktree symbolic-ref --short HEAD).Trim() -ne
    "main"
) {
    throw "Resolved integration worktree is not on main."
}

if (
    (git -C $mainWorktree rev-parse HEAD).Trim() -ne
    $governanceMain
) {
    throw "Resolved main worktree HEAD mismatch."
}

Write-Host "Local main integration worktree: PASS"

$integrationAttempted = $false

try {
    Write-Host "`n=== APPLY REVIEWED WO-005 COMMITS LINEARLY ==="

    $integrationAttempted = $true

    $technicalIntegrated = Apply-SourceCommit `
        -Worktree $mainWorktree `
        -SourceCommit $candidateCommit `
        -ExpectedCurrentHead $governanceMain `
        -ExpectedPaths $deliverablePaths `
        -Label "1/5 Technical candidate"

    Write-Host "1/5 Technical candidate integrated:" $technicalIntegrated.Integrated

    $designationIntegrated = Apply-SourceCommit `
        -Worktree $mainWorktree `
        -SourceCommit $designationCommit `
        -ExpectedCurrentHead $technicalIntegrated.Integrated `
        -ExpectedPaths $governancePaths `
        -Label "2/5 Candidate designation"

    Write-Host "2/5 Candidate designation integrated:" $designationIntegrated.Integrated

    $architectureIntegrated = Apply-SourceCommit `
        -Worktree $mainWorktree `
        -SourceCommit $architectureReviewCommit `
        -ExpectedCurrentHead $designationIntegrated.Integrated `
        -ExpectedPaths $governancePaths `
        -Label "3/5 Architecture review"

    Write-Host "3/5 Architecture review integrated:" $architectureIntegrated.Integrated

    $qaIntegrated = Apply-SourceCommit `
        -Worktree $mainWorktree `
        -SourceCommit $qaReviewCommit `
        -ExpectedCurrentHead $architectureIntegrated.Integrated `
        -ExpectedPaths $governancePaths `
        -Label "4/5 QA review"

    Write-Host "4/5 QA review integrated:" $qaIntegrated.Integrated

    $verdictIntegrated = Apply-SourceCommit `
        -Worktree $mainWorktree `
        -SourceCommit $finalVerdictCommit `
        -ExpectedCurrentHead $qaIntegrated.Integrated `
        -ExpectedPaths $governancePaths `
        -Label "5/5 Final review verdict"

    Write-Host "5/5 Final review verdict integrated:" $verdictIntegrated.Integrated

    $finalLocalMain = (
        git -C $mainWorktree rev-parse HEAD
    ).Trim()

    Write-Host "`n=== VALIDATE FINAL LOCAL MAIN ==="

    if ($finalLocalMain -ne $verdictIntegrated.Integrated) {
        throw "Final local main does not equal the integrated verdict commit."
    }

    $integratedCount = [int](
        git -C $mainWorktree rev-list `
            --count `
            "$governanceMain..$finalLocalMain"
    ).Trim()

    if ($integratedCount -ne 5) {
        throw "Expected exactly five integrated commits, found $integratedCount."
    }

    $finalChangedPaths = @(
        git -C $mainWorktree diff `
            --name-only `
            $governanceMain `
            $finalLocalMain
    )

    Assert-ExactPathSet `
        -Actual $finalChangedPaths `
        -Expected $finalExpectedPaths `
        -Label "Final WO-005 local integration"

    Assert-BlobIdentity `
        -Repository $mainWorktree `
        -SourceCommit $candidateCommit `
        -IntegratedCommit $finalLocalMain `
        -Paths $deliverablePaths `
        -Label "Final technical content"

    Assert-BlobIdentity `
        -Repository $mainWorktree `
        -SourceCommit $finalVerdictCommit `
        -IntegratedCommit $finalLocalMain `
        -Paths $governancePaths `
        -Label "Final governance verdict content"

    Invoke-Native {
        git -C $mainWorktree diff `
            --check `
            $governanceMain `
            $finalLocalMain
    } "Final integrated whitespace validation"

    $forbiddenChanges = @(
        git -C $mainWorktree diff `
            --name-only `
            $governanceMain `
            $finalLocalMain `
            -- `
            aegis_os `
            tests `
            pyproject.toml `
            .github
    )

    if ($forbiddenChanges.Count -ne 0) {
        throw "Final local integration contains forbidden runtime, test, dependency, or CI changes."
    }

    if (@(git -C $mainWorktree status --short).Count -ne 0) {
        throw "Local main worktree is dirty after integration."
    }

    Write-Host "Five-commit linear sequence, six-path final boundary, and blob identity: PASS"

    Write-Host "`n=== VERIFY REMOTE PRESERVATION ==="

    Invoke-Native {
        git -C $repo fetch origin `
            "+refs/heads/main:refs/remotes/origin/main"
    } "Post-integration remote refresh"

    $originMainAfter = (
        git -C $repo rev-parse refs/remotes/origin/main
    ).Trim()

    $liveMainAfter = Get-LiveRemoteMain $repo

    if ($originMainAfter -ne $governanceMain) {
        throw "origin/main changed during local integration."
    }

    if ($liveMainAfter -ne $governanceMain) {
        throw "Live remote main changed during local integration."
    }

    if (
        (git -C $repo rev-parse refs/heads/main).Trim() -ne
        $finalLocalMain
    ) {
        throw "Local main reference does not match the integrated final commit."
    }

    Assert-AllWorktreesClean `
        -Repository $repo `
        -Label "Final"

    Write-Host "Remote main unchanged; local main integrated: PASS"

    Write-Host "`n=== WRITE LOCAL INTEGRATION MANIFEST ==="

    New-Item `
        -ItemType Directory `
        -Path $logDirectory `
        -Force | Out-Null

    $manifest = @"
AEGIS WO-005 Local Integration
==============================

Date: 2026-07-31

Starting local/remote governance main:
$governanceMain

Architectural base:
$architecturalBase

Local main worktree:
$mainWorktree

Source -> locally integrated commit mapping:

1. Technical candidate
Source: $($technicalIntegrated.Source)
Integrated: $($technicalIntegrated.Integrated)
Parent: $($technicalIntegrated.Parent)
Subject: $($technicalIntegrated.Subject)

2. Candidate designation
Source: $($designationIntegrated.Source)
Integrated: $($designationIntegrated.Integrated)
Parent: $($designationIntegrated.Parent)
Subject: $($designationIntegrated.Subject)

3. Architecture review
Source: $($architectureIntegrated.Source)
Integrated: $($architectureIntegrated.Integrated)
Parent: $($architectureIntegrated.Parent)
Subject: $($architectureIntegrated.Subject)

4. QA review
Source: $($qaIntegrated.Source)
Integrated: $($qaIntegrated.Integrated)
Parent: $($qaIntegrated.Parent)
Subject: $($qaIntegrated.Subject)

5. Final review verdict
Source: $($verdictIntegrated.Source)
Integrated: $($verdictIntegrated.Integrated)
Parent: $($verdictIntegrated.Parent)
Subject: $($verdictIntegrated.Subject)

Final local main:
$finalLocalMain

Remote main preserved at:
$liveMainAfter

Final changed paths:
$($finalChangedPaths -join "`r`n")

Validation:
- Linear integrated commit count: 5
- Merge commits: 0
- Final changed path count: 6
- Technical blobs equal reviewed candidate: PASS
- Governance blobs equal reviewed final verdict: PASS
- Runtime changes: 0
- Test changes: 0
- Dependency changes: 0
- CI changes: 0
- Whitespace validation: PASS
- Worktrees clean: PASS
- Push performed: NO
- origin/main changed: NO
- Live remote main changed: NO
- Publication authorized: NO
- Runtime implementation authorized: NO
- Tag or release created: NO
- Worktree cleanup performed: NO
"@

    [System.IO.File]::WriteAllText(
        $manifestPath,
        $manifest,
        $utf8NoBom
    )

    Write-Host "`n=== WO-005 LOCAL INTEGRATION RESULT ==="

    [pscustomobject]@{
        StartingGovernanceMain = $governanceMain
        ArchitecturalBase = $architecturalBase
        MainWorktree = $mainWorktree
        TechnicalSource = $technicalIntegrated.Source
        TechnicalIntegrated = $technicalIntegrated.Integrated
        DesignationSource = $designationIntegrated.Source
        DesignationIntegrated = $designationIntegrated.Integrated
        ArchitectureReviewSource = $architectureIntegrated.Source
        ArchitectureReviewIntegrated = $architectureIntegrated.Integrated
        QAReviewSource = $qaIntegrated.Source
        QAReviewIntegrated = $qaIntegrated.Integrated
        FinalVerdictSource = $verdictIntegrated.Source
        FinalVerdictIntegrated = $verdictIntegrated.Integrated
        FinalLocalMain = $finalLocalMain
        IntegratedCommitCount = $integratedCount
        FinalChangedPathCount = $finalChangedPaths.Count
        TechnicalBlobIdentity = "PASS"
        GovernanceBlobIdentity = "PASS"
        RuntimeChanges = 0
        TestChanges = 0
        DependencyChanges = 0
        CIChanges = 0
        OriginMain = $originMainAfter
        LiveRemoteMain = $liveMainAfter
        RemoteMutation = "NONE"
        PushPerformed = $false
        MergeCommits = 0
        WorktreesClean = $true
        Manifest = $manifestPath
        PublicationAuthorized = $false
        RuntimeImplementationAuthorized = $false
        FinalStatus = "WO-005 LOCALLY INTEGRATED - PUBLICATION NOT AUTHORIZED"
    } | Format-List

    Write-Host "Final integrated paths:"
    $finalChangedPaths | ForEach-Object { Write-Host " - $_" }

    Write-Host "`nWO-005 LOCAL INTEGRATION: COMPLETE"
    Write-Host "Local main contains the reviewed five-commit WO-005 sequence."
    Write-Host "Remote main remains unchanged at $governanceMain."
    Write-Host "No push, runtime implementation, tag, release, ruleset change, or worktree cleanup was performed."
}
catch {
    Write-Host "`n=== LOCAL INTEGRATION FAILURE: RESTORE MAIN ==="

    if ($integrationAttempted -and $mainWorktree) {
        $restored = Restore-LocalMain `
            -Worktree $mainWorktree `
            -Target $governanceMain

        Write-Host "Local main restored to governance base:" $restored
    }

    try {
        $liveAfterFailure = Get-LiveRemoteMain $repo
        Write-Host "Live remote main after failure:" $liveAfterFailure
    }
    catch {
        Write-Host "Live remote main could not be re-read after failure."
    }

    throw
}
