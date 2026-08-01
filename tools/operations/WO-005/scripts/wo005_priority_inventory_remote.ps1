$ErrorActionPreference = "Stop"

if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$repo = "$env:USERPROFILE\Projects\aegis-platform"
$expectedRemoteMain = "be7502f73b51808d54728f912ead46ad0073c7b9"
$analysisRef = "refs/remotes/origin/main"

function Invoke-GitRead {
    param(
        [scriptblock]$Command,
        [string]$Label,
        [switch]$AllowNoMatch
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

    if ($exitCode -ne 0 -and -not ($AllowNoMatch -and $exitCode -eq 1)) {
        throw "$Label failed with exit code $exitCode."
    }

    return $output
}

Write-Host "`n=== REFRESH REMOTE MAIN ==="

if (-not (Test-Path -LiteralPath $repo)) {
    throw "Repository not found: $repo"
}

$localMainBefore = (git -C $repo rev-parse refs/heads/main).Trim()
$currentHeadBefore = (git -C $repo rev-parse HEAD).Trim()
$currentBranchBefore = (git -C $repo branch --show-current).Trim()

git -C $repo fetch origin "+refs/heads/main:refs/remotes/origin/main"

if ($LASTEXITCODE -ne 0) {
    throw "Unable to refresh origin/main."
}

$originMain = (git -C $repo rev-parse $analysisRef).Trim()

$remoteLines = @(
    git -C $repo ls-remote --heads origin refs/heads/main
)

if ($LASTEXITCODE -ne 0 -or $remoteLines.Count -ne 1) {
    throw "Unable to resolve exactly one live remote main."
}

$liveMain = (($remoteLines[0] -split "\s+")[0]).Trim()

[pscustomobject]@{
    ExpectedRemoteMain = $expectedRemoteMain
    OriginMain         = $originMain
    LiveRemoteMain     = $liveMain
    LocalMainObserved  = $localMainBefore
    AnalysisReference  = $analysisRef
} | Format-List

if ($originMain -ne $expectedRemoteMain) {
    throw "Refreshed origin/main does not match the WO-004 closure."
}

if ($liveMain -ne $expectedRemoteMain) {
    throw "Live remote main does not match the WO-004 closure."
}

Write-Host "Remote main identity: PASS"
Write-Host "Local main is not required and will not be modified."

Write-Host "`n=== GOVERNANCE WORK-ORDER INVENTORY ==="

$workOrderPaths = @(
    Invoke-GitRead {
        git -C $repo ls-tree -r --name-only $analysisRef governance/work-orders
    } "Work-order inventory" |
        Where-Object { $_ -like "*.md" } |
        Sort-Object
)

if ($workOrderPaths.Count -eq 0) {
    throw "No governance work orders were found."
}

$workOrderInventory = foreach ($path in $workOrderPaths) {
    $content = (
        Invoke-GitRead {
            git -C $repo show "${analysisRef}:$path"
        } "Reading $path"
    ) -join "`n"

    $titleMatch = [regex]::Match($content, '(?m)^#\s+(.+)$')
    $statusMatch = [regex]::Match(
        $content,
        '(?mi)^\*{0,2}Status:\*{0,2}\s*(.+)$'
    )
    $dispositionMatch = [regex]::Match(
        $content,
        '(?mi)^(?:Final disposition|Disposition|Final status):\s*(.+)$'
    )

    [pscustomobject]@{
        File = [System.IO.Path]::GetFileName($path)
        Title = if ($titleMatch.Success) {
            $titleMatch.Groups[1].Value.Trim()
        }
        else {
            "(title not detected)"
        }
        Status = if ($statusMatch.Success) {
            $statusMatch.Groups[1].Value.Trim()
        }
        elseif ($dispositionMatch.Success) {
            $dispositionMatch.Groups[1].Value.Trim()
        }
        else {
            "(status not detected)"
        }
    }
}

$workOrderInventory | Format-Table -AutoSize -Wrap

Write-Host "`n=== NON-CLOSED WORK ORDERS ==="

$nonClosed = @(
    $workOrderInventory |
        Where-Object {
            $_.Status -notmatch '(?i)\bCLOSED\b' -and
            $_.Status -notmatch '(?i)\bCOMPLETE(?:D)?\b' -and
            $_.Status -notmatch '(?i)\bEXECUTED\b'
        }
)

if ($nonClosed.Count -eq 0) {
    Write-Host "No clearly active work order remains."
}
else {
    $nonClosed | Format-Table -AutoSize -Wrap
}

Write-Host "`n=== DEFERRED AND FUTURE-WORK EVIDENCE ==="

$futureExpression = @(
    "separate work order",
    "future work",
    "future phase",
    "next phase",
    "deferred",
    "not implemented",
    "not yet implemented",
    "follow-up",
    "technical debt"
) -join "|"

$futureEvidence = @(
    Invoke-GitRead {
        git -C $repo grep -n -I -i -E $futureExpression $analysisRef -- `
            aegis_os docs governance tests
    } "Future-work evidence search" -AllowNoMatch
)

if ($futureEvidence.Count -eq 0) {
    Write-Host "No explicit future-work evidence found."
}
else {
    $futureEvidence |
        Select-Object -First 200 |
        ForEach-Object { Write-Host $_ }

    if ($futureEvidence.Count -gt 200) {
        Write-Host "... $($futureEvidence.Count - 200) additional matches omitted."
    }
}

Write-Host "`n=== TODO, FIXME, AND PLACEHOLDER INVENTORY ==="

$placeholderEvidence = @(
    Invoke-GitRead {
        git -C $repo grep -n -I -E `
            "TODO|FIXME|NotImplemented|not_implemented|pass[[:space:]]*(#.*)?$" `
            $analysisRef -- aegis_os tests docs
    } "Placeholder inventory" -AllowNoMatch
)

if ($placeholderEvidence.Count -eq 0) {
    Write-Host "No TODO, FIXME, or explicit placeholder evidence found."
}
else {
    $placeholderEvidence |
        Select-Object -First 200 |
        ForEach-Object { Write-Host $_ }

    if ($placeholderEvidence.Count -gt 200) {
        Write-Host "... $($placeholderEvidence.Count - 200) additional matches omitted."
    }
}

Write-Host "`n=== ARCHITECTURAL PLACEHOLDERS BY AREA ==="

$areas = @(
    "governance",
    "evaluation",
    "learning",
    "memory",
    "persistence",
    "execution",
    "provider",
    "model"
)

$areaSummary = foreach ($area in $areas) {
    $matches = @(
        Invoke-GitRead {
            git -C $repo grep -n -I -i $area $analysisRef -- aegis_os docs
        } "Area search: $area" -AllowNoMatch
    )

    $placeholderMatches = @(
        $matches |
            Where-Object {
                $_ -match '(?i)(not implemented|deferred|future|placeholder|separate work order|TODO|FIXME)'
            }
    )

    [pscustomobject]@{
        Area = $area
        TotalReferences = $matches.Count
        DeferredOrPlaceholderReferences = $placeholderMatches.Count
    }
}

$sortProperties = @(
    @{
        Expression = { $_.DeferredOrPlaceholderReferences }
        Descending = $true
    },
    @{
        Expression = { $_.TotalReferences }
        Descending = $true
    }
)

$sortedAreaSummary = @(
    $areaSummary | Sort-Object -Property $sortProperties
)

$sortedAreaSummary | Format-Table -AutoSize

Write-Host "`n=== TOP PRIORITY EVIDENCE ==="

$rankedAreas = @(
    $sortedAreaSummary |
        Where-Object { $_.DeferredOrPlaceholderReferences -gt 0 }
)

if ($rankedAreas.Count -eq 0) {
    Write-Host "No next priority can be inferred automatically."
}
else {
    $rankedAreas |
        Select-Object -First 5 |
        Format-Table -AutoSize
}

Write-Host "`n=== FINAL PRESERVATION ==="

$localMainAfter = (git -C $repo rev-parse refs/heads/main).Trim()
$currentHeadAfter = (git -C $repo rev-parse HEAD).Trim()
$currentBranchAfter = (git -C $repo branch --show-current).Trim()
$originMainAfter = (git -C $repo rev-parse $analysisRef).Trim()

if ($localMainAfter -ne $localMainBefore) {
    throw "Local main changed during the inventory."
}

if ($currentHeadAfter -ne $currentHeadBefore) {
    throw "Current worktree HEAD changed during the inventory."
}

if ($currentBranchAfter -ne $currentBranchBefore) {
    throw "Current worktree branch changed during the inventory."
}

if ($originMainAfter -ne $expectedRemoteMain) {
    throw "origin/main changed unexpectedly after inventory."
}

[pscustomobject]@{
    WorkOrderCount = $workOrderInventory.Count
    NonClosedWorkOrderCount = $nonClosed.Count
    FutureEvidenceCount = $futureEvidence.Count
    PlaceholderEvidenceCount = $placeholderEvidence.Count
    AnalysisSource = $originMainAfter
    RepositoryMutation = "NONE"
    LocalMainUnchanged = $true
    CurrentHeadUnchanged = $true
    CurrentBranchUnchanged = $true
    Result = "WO-005 PRIORITY INVENTORY COMPLETE"
} | Format-List

Write-Host "WO-005 PRIORITY INVENTORY: COMPLETE"
Write-Host "No file, commit, branch, worktree, local main, or remote reference was modified."
