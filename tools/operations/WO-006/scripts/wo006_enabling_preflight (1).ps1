$ErrorActionPreference = "Stop"

if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$repo = "$env:USERPROFILE\Projects\aegis-platform"
$expectedMain = "cfae92111eeb5355873a8c32c649514853564743"

$specPath = "docs/specifications/v0.5-phase-b-environment-interaction-layer.md"
$adrPath = "docs/adr/ADR-006-environment-interaction-layer.md"
$wo006Path = "governance/work-orders/WO-006_ENVIRONMENT_INTERACTION_LAYER_SIMULATION_RUNTIME.md"

$operationsPath = "tools/operations"
$wo004ScriptsPath = "tools/operations/WO-004/scripts"
$wo005ScriptsPath = "tools/operations/WO-005/scripts"
$wo006ScriptsPath = "tools/operations/WO-006/scripts"

function Invoke-Native {
    param(
        [scriptblock]$Command,
        [string]$Label,
        [switch]$AllowFailure
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

    if (-not $AllowFailure -and $exitCode -ne 0) {
        throw "$Label failed with exit code $exitCode."
    }

    return [pscustomobject]@{
        Output = $output
        ExitCode = $exitCode
    }
}

function Get-LiveRemoteMain {
    param([string]$Repository)

    $result = Invoke-Native {
        git -C $Repository ls-remote --heads origin refs/heads/main
    } "Live remote main lookup"

    if ($result.Output.Count -ne 1) {
        throw "Expected exactly one live remote main reference."
    }

    return (($result.Output[0] -split "\s+")[0]).Trim()
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

function Get-CommitText {
    param(
        [string]$Repository,
        [string]$Commit,
        [string]$Path
    )

    $result = Invoke-Native {
        git -C $Repository show "${Commit}:$Path"
    } "Read $Path from $Commit"

    return ($result.Output -join "`n")
}

function Test-TreePath {
    param(
        [string]$Repository,
        [string]$Commit,
        [string]$Path
    )

    $result = Invoke-Native {
        git -C $Repository cat-file -e "${Commit}:$Path"
    } "Tree path lookup" -AllowFailure

    return ($result.ExitCode -eq 0)
}

function Get-ScriptCount {
    param([string]$AbsolutePath)

    if (-not (Test-Path -LiteralPath $AbsolutePath)) {
        return 0
    }

    return @(
        Get-ChildItem `
            -LiteralPath $AbsolutePath `
            -File `
            -Filter "*.ps1" `
            -ErrorAction SilentlyContinue
    ).Count
}

Write-Host "`n=== WO-006 ENABLING PREFLIGHT ==="

if (-not (Test-Path -LiteralPath $repo)) {
    throw "Repository not found: $repo"
}

Invoke-Native {
    git -C $repo fetch origin `
        "+refs/heads/main:refs/remotes/origin/main"
} "Remote main refresh" | Out-Null

$localMain = (
    git -C $repo rev-parse refs/heads/main
).Trim()

$originMain = (
    git -C $repo rev-parse refs/remotes/origin/main
).Trim()

$liveMain = Get-LiveRemoteMain $repo

$mainIdentityPass = (
    $localMain -eq $expectedMain -and
    $originMain -eq $expectedMain -and
    $liveMain -eq $expectedMain
)

Write-Host "Local main :" $localMain
Write-Host "Origin main:" $originMain
Write-Host "Live main  :" $liveMain
Write-Host "Closed WO-005 identity:" $(if ($mainIdentityPass) { "PASS" } else { "FAIL" })

Write-Host "`n=== WORKTREE AND OPERATIONS ARCHIVE INVENTORY ==="

$worktreeRecords = @()
$dirtyWorktreeCount = 0

foreach ($worktree in @(Get-RegisteredWorktrees $repo)) {
    $statusLines = @(
        git -C $worktree.Path status --short
    )

    $isClean = ($statusLines.Count -eq 0)

    if (-not $isClean) {
        $dirtyWorktreeCount++
    }

    $worktreeRecords += [pscustomobject]@{
        Path = $worktree.Path
        Branch = $worktree.Branch
        Clean = $isClean
        ChangeCount = $statusLines.Count
    }

    Write-Host ""
    Write-Host "Worktree:" $worktree.Path
    Write-Host "Branch  :" $worktree.Branch
    Write-Host "Clean   :" $isClean

    foreach ($line in $statusLines) {
        Write-Host "  $line"
    }
}

$wo004Absolute = Join-Path $repo $wo004ScriptsPath
$wo005Absolute = Join-Path $repo $wo005ScriptsPath
$wo006Absolute = Join-Path $repo $wo006ScriptsPath

$wo004ScriptCount = Get-ScriptCount $wo004Absolute
$wo005ScriptCount = Get-ScriptCount $wo005Absolute
$wo006ScriptCount = Get-ScriptCount $wo006Absolute

$operationsStatus = @(
    git -C $repo status --short -- $operationsPath
)

$operationsTrackedAtMain = Test-TreePath `
    -Repository $repo `
    -Commit $expectedMain `
    -Path $operationsPath

Write-Host ""
Write-Host "WO-004 scripts in repository folder:" $wo004ScriptCount
Write-Host "WO-005 scripts in repository folder:" $wo005ScriptCount
Write-Host "WO-006 scripts in repository folder:" $wo006ScriptCount
Write-Host "tools/operations tracked at published main:" $operationsTrackedAtMain
Write-Host "Current tools/operations status entries:" $operationsStatus.Count

foreach ($line in $operationsStatus) {
    Write-Host "  $line"
}

Write-Host "`n=== WO-006 GOVERNANCE EXISTENCE CHECK ==="

$wo006ExistsAtMain = Test-TreePath `
    -Repository $repo `
    -Commit $expectedMain `
    -Path $wo006Path

Write-Host "WO-006 work order exists at current main:" $wo006ExistsAtMain

Write-Host "`n=== ACCEPTED SPECIFICATION CONSISTENCY CHECK ==="

$specification = Get-CommitText `
    -Repository $repo `
    -Commit $expectedMain `
    -Path $specPath

$adr = Get-CommitText `
    -Repository $repo `
    -Commit $expectedMain `
    -Path $adrPath

$checks = [ordered]@{
    SpecificationHeaderAccepted = $specification.Contains(
        "- **Status:** Accepted implementation specification"
    )
    ADR006HeaderAccepted = $adr.Contains(
        "- **Status:** Accepted"
    )
    Section47RequiresPostRuntimeAcceptance = $specification.Contains(
        "ADR-006 may move from Proposed to Accepted only after this specification is"
    )
    Section47ProhibitsStatusChange = $specification.Contains(
        "This task MUST NOT change ADR-006 status."
    )
    DecisionTableSaysADRRemainsProposed = $specification.Contains(
        "Remains Proposed until runtime acceptance evidence"
    )
    ImplementationOrderStillRequiresADRReview = $specification.Contains(
        "14. ADR-006 review."
    )
    GuardrailRequiresStopOnContradiction = $specification.Contains(
        "If an internal contradiction is found, work SHALL"
    ) -and $specification.Contains(
        "stop and the exact conflicting sections SHALL be reported."
    )
}

foreach ($entry in $checks.GetEnumerator()) {
    Write-Host "$($entry.Key): $($entry.Value)"
}

$contradictionDetected = (
    $checks.SpecificationHeaderAccepted -and
    $checks.ADR006HeaderAccepted -and
    (
        $checks.Section47RequiresPostRuntimeAcceptance -or
        $checks.DecisionTableSaysADRRemainsProposed
    )
)

$blockingIssues = @()

if (-not $mainIdentityPass) {
    $blockingIssues += "MAIN_IDENTITY_MISMATCH"
}

if ($wo006ExistsAtMain) {
    $blockingIssues += "WO006_ALREADY_EXISTS"
}

if ($contradictionDetected) {
    $blockingIssues += "ACCEPTED_SPECIFICATION_ADR_STATUS_CONTRADICTION"
}

if ($dirtyWorktreeCount -gt 0) {
    $blockingIssues += "DIRTY_WORKTREE_STATE"
}

if ($operationsStatus.Count -gt 0) {
    $blockingIssues += "OPERATIONS_ARCHIVE_NOT_RECONCILED_WITH_MAIN"
}

Write-Host "`n=== WO-006 ENABLING PREFLIGHT RESULT ==="

[pscustomobject]@{
    ExpectedMain = $expectedMain
    LocalMain = $localMain
    OriginMain = $originMain
    LiveRemoteMain = $liveMain
    MainIdentityPass = $mainIdentityPass
    WO006Exists = $wo006ExistsAtMain
    SpecificationHeaderStatus = $(if ($checks.SpecificationHeaderAccepted) { "ACCEPTED" } else { "UNEXPECTED" })
    ADR006Status = $(if ($checks.ADR006HeaderAccepted) { "ACCEPTED" } else { "UNEXPECTED" })
    SpecificationContradictionDetected = $contradictionDetected
    DirtyWorktreeCount = $dirtyWorktreeCount
    OperationsArchiveTrackedAtPublishedMain = $operationsTrackedAtMain
    OperationsArchiveStatusEntries = $operationsStatus.Count
    WO004ScriptCount = $wo004ScriptCount
    WO005ScriptCount = $wo005ScriptCount
    WO006ScriptCount = $wo006ScriptCount
    BlockingIssueCount = $blockingIssues.Count
    BlockingIssues = ($blockingIssues -join ", ")
    RepositoryMutationPerformed = $false
    CommitCreated = $false
    PushPerformed = $false
    RuntimeImplementationAuthorized = $false
    FinalStatus = $(
        if ($blockingIssues.Count -eq 0) {
            "WO-006 READY FOR GOVERNANCE AUTHORIZATION DRAFT"
        }
        else {
            "WO-006 ENABLING BLOCKED PENDING RECONCILIATION"
        }
    )
} | Format-List

if ($blockingIssues.Count -gt 0) {
    Write-Host "Blocking issues:"
    $blockingIssues | ForEach-Object { Write-Host " - $_" }
}

Write-Host "`nWO-006 PREFLIGHT: COMPLETE"
Write-Host "No source, governance, main, remote, tag, release, ruleset, or worktree cleanup mutation was performed."
