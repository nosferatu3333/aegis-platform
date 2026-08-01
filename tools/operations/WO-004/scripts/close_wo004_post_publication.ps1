$ErrorActionPreference = "Stop"

if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$repo = "$env:USERPROFILE\Projects\aegis-platform"
$impl = "$env:USERPROFILE\Projects\aegis-platform-wo-004"
$gov = "$env:USERPROFILE\Projects\aegis-platform-wo-004-governance"
$integration = "$env:USERPROFILE\Projects\aegis-platform-wo-004-integration"
$closure = "$env:USERPROFILE\Projects\aegis-platform-wo-004-closure"

$closureBranch = "governance/wo-004-post-publication-closure"
$commitSubject = "Close WO-004 after main publication"

$publishedMain = "e8de24afa14b564c28ebecd6564e0c111e134924"
$candidateCommit = "ce9d17429edc186db74e389e39f5ce6e0677cb35"
$reviewCommit = "59ed6530210fc296b50c8d64b7372c08b9db302b"

$workOrderRel = "governance/work-orders/WO-004_KERNEL_CANONICAL_RUNTIME_CONVERGENCE.md"
$traceRel = "governance/TRACEABILITY.md"
$expectedPaths = @($workOrderRel, $traceRel)
$utf8 = New-Object System.Text.UTF8Encoding($false)

function Run-Native {
    param([scriptblock]$Command, [string]$Label)
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE."
    }
}

function Get-RemoteMain {
    param([string]$Repository)
    $lines = @(& git -C $Repository ls-remote --heads origin refs/heads/main)
    if ($LASTEXITCODE -ne 0 -or $lines.Count -ne 1) {
        throw "Unable to resolve live remote main."
    }
    return (($lines[0] -split "\s+")[0]).Trim()
}

function Assert-ExactPaths {
    param([string[]]$Actual, [string[]]$Expected, [string]$Label)
    $unexpected = @($Actual | Where-Object { $_ -notin $Expected })
    $missing = @($Expected | Where-Object { $_ -notin $Actual })
    if ($Actual.Count -ne $Expected.Count -or $unexpected.Count -gt 0 -or $missing.Count -gt 0) {
        Write-Host "$Label actual paths:"
        $Actual | ForEach-Object { Write-Host " - $_" }
        throw "$Label path boundary mismatch."
    }
}

Write-Host "`n=== CLOSURE PREFLIGHT ==="

foreach ($path in @($repo, $impl, $gov, $integration)) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Required path not found: $path"
    }
}

$originalBranch = (git -C $repo branch --show-current).Trim()
$originalHead = (git -C $repo rev-parse HEAD).Trim()

Run-Native { git -C $repo fetch origin main } "Initial fetch"

$remoteBefore = Get-RemoteMain $repo
$trackingBefore = (git -C $repo rev-parse refs/remotes/origin/main).Trim()
$localMainBefore = (git -C $repo rev-parse refs/heads/main).Trim()
$integrationHead = (git -C $integration rev-parse HEAD).Trim()

foreach ($sha in @($remoteBefore, $trackingBefore, $localMainBefore, $integrationHead)) {
    if ($sha -ne $publishedMain) {
        throw "Published identity mismatch before closure."
    }
}

if ((git -C $impl rev-parse HEAD).Trim() -ne $candidateCommit) {
    throw "Implementation candidate HEAD mismatch."
}

if ((git -C $gov rev-parse HEAD).Trim() -ne $reviewCommit) {
    throw "Governance review HEAD mismatch."
}

foreach ($worktree in @($repo, $impl, $gov, $integration)) {
    if (@(git -C $worktree status --short).Count -ne 0) {
        throw "Worktree is not clean: $worktree"
    }
}

if (Test-Path -LiteralPath $closure) {
    throw "Closure worktree already exists: $closure"
}

if (@(git -C $repo branch --list $closureBranch).Count -ne 0) {
    throw "Closure branch already exists: $closureBranch"
}

if (@(git -C $repo worktree list --porcelain | Select-String -SimpleMatch "branch refs/heads/main").Count -ne 0) {
    throw "Local main is checked out in a worktree."
}

Write-Host "Published state and worktrees: PASS"

Write-Host "`n=== CREATE CLOSURE WORKTREE ==="
Run-Native {
    git -C $repo worktree add -b $closureBranch $closure $publishedMain
} "Closure worktree creation"

$workOrderPath = Join-Path $closure $workOrderRel
$tracePath = Join-Path $closure $traceRel

try {
    Write-Host "`n=== UPDATE GOVERNANCE RECORDS ==="

    $workOrder = [System.IO.File]::ReadAllText($workOrderPath) -replace "`r`n", "`n"
    $trace = [System.IO.File]::ReadAllText($tracePath) -replace "`r`n", "`n"

    if ($workOrder.Contains("## Post-publication closure")) {
        throw "WO-004 closure already exists."
    }

    if ($trace.Contains("## TR-006 Post-Publication Closure")) {
        throw "TR-006 closure already exists."
    }

    $statusRegex = [regex]::new('(?m)^\*\*Status:\*\*.*$')
    $integrationRegex = [regex]::new('(?m)^\*\*Integration authority:\*\*.*$')
    $publicationRegex = [regex]::new('(?m)^\*\*Remote-publication authority:\*\*.*$')

    $workOrder = $statusRegex.Replace($workOrder, '**Status:** CLOSED - PUBLISHED TO MAIN', 1)
    $workOrder = $integrationRegex.Replace($workOrder, '**Integration authority:** EXECUTED - COMPLETE', 1)
    $workOrder = $publicationRegex.Replace($workOrder, '**Remote-publication authority:** EXECUTED - COMPLETE', 1)

    $newDisposition = @'
## Current Disposition

```text
WO-004: CLOSED - PUBLISHED TO MAIN
Authoritative base: 8514de1f4e1bafb73748ec74a9b29e8b2f83d952
Implementation scope: COMPLETED
Candidate designated: ce9d17429edc186db74e389e39f5ce6e0677cb35
QA review: PASS
Architecture review: PASS
Integration authority: EXECUTED - COMPLETE
Publication authority: EXECUTED - COMPLETE
Published main: e8de24afa14b564c28ebecd6564e0c111e134924
```

'@

    $dispositionRegex = [regex]::new('(?s)## Current Disposition\s+```text.*?```\s*(?=## Candidate review verdict)')
    if (-not $dispositionRegex.IsMatch($workOrder)) {
        throw "Current disposition block was not found."
    }
    $workOrder = $dispositionRegex.Replace($workOrder, $newDisposition, 1)

    $workOrderClosure = @'

## Post-publication closure

- Closure date: 2026-07-31
- Authoritative base: `8514de1f4e1bafb73748ec74a9b29e8b2f83d952`
- Authorization source: `1aa7c27248438662272cab22e1b63797845ab6da`
- Reviewed candidate: `ce9d17429edc186db74e389e39f5ce6e0677cb35`
- Governance review source: `59ed6530210fc296b50c8d64b7372c08b9db302b`
- Published integration head: `e8de24afa14b564c28ebecd6564e0c111e134924`
- Destination: `refs/heads/main`
- Publication result: **PASS - STRICT FAST-FORWARD**
- Final status: **CLOSED - PUBLISHED TO MAIN**

### Published linear sequence

1. `1b00418c87293f607dfdf76df1aa6325e6610ae7` - Authorize WO-004 kernel runtime convergence
2. `9a39aff6ecd991eade808628d1931ccfd4ac22b3` - Converge Kernel on canonical runtime
3. `e8de24afa14b564c28ebecd6564e0c111e134924` - Record WO-004 candidate review verdict

### Final evidence

- Live remote `main`, `origin/main`, local `main`, and integration HEAD matched the published head.
- Publication used a strict fast-forward.
- No force-push, merge commit, tag, release, or cleanup occurred.
- Integrated repository suite: 179 passed.
- Python 3.11 reviewed-candidate suite: 179 passed.
- Ruff lint, Ruff format, and dependency integrity passed.
- All related worktrees were clean and the original worktree was unchanged.

### Final architectural disposition

The normal application entry path now uses `Kernel.process_task()`, the
configured canonical `CognitiveRuntime`, the canonical request pipeline,
optional simulated execution, conformance validation, and
`CanonicalRuntimeResult`.

The historical `Kernel.process_goal()` path remains available only through the
explicit lazy compatibility adapter. No real execution was introduced.

### Closure boundary

This closure is governance-only. It changes no implementation, test, runtime,
API, benchmark, dependency, CI, ruleset, tag, or release content.

WO-004 is complete. This record grants no further implementation, integration,
publication, cleanup, release, deployment, tag, ruleset, or branch-removal
authority.
'@

    $traceClosure = @'

## TR-006 Post-Publication Closure

- Work order: WO-004 - Kernel Canonical Runtime Convergence
- Closure date: 2026-07-31
- Authorization commit: `1aa7c27248438662272cab22e1b63797845ab6da`
- Reviewed candidate: `ce9d17429edc186db74e389e39f5ce6e0677cb35`
- Candidate-review record: `59ed6530210fc296b50c8d64b7372c08b9db302b`
- Published integration head: `e8de24afa14b564c28ebecd6564e0c111e134924`
- Final local `main`: `e8de24afa14b564c28ebecd6564e0c111e134924`
- Final `origin/main`: `e8de24afa14b564c28ebecd6564e0c111e134924`
- Final live remote `main`: `e8de24afa14b564c28ebecd6564e0c111e134924`
- Publication result: **PASS - STRICT FAST-FORWARD**
- Final disposition: **CLOSED - REMOTE MAIN PUBLICATION COMPLETE**
- Force-push: no
- Merge commit: no
- Tag or release: none
- Worktree preservation: passed
- Further authority: none

The exact reviewed implementation and governance records were published as a
linear three-commit fast-forward from the authoritative base. This closure
records the completed state only and grants no additional authority.
'@

    $workOrder = $workOrder.TrimEnd() + $workOrderClosure + "`n"
    $trace = $trace.TrimEnd() + $traceClosure + "`n"

    [System.IO.File]::WriteAllText($workOrderPath, $workOrder, $utf8)
    [System.IO.File]::WriteAllText($tracePath, $trace, $utf8)

    Write-Host "Governance closure content: ADDED"

    Write-Host "`n=== VALIDATE AND COMMIT CLOSURE ==="

    $changed = @(git -C $closure status --short | ForEach-Object { $_.Substring(3) })
    Assert-ExactPaths $changed $expectedPaths "Closure worktree"

    Run-Native { git -C $closure diff --check } "Closure whitespace check"
    Run-Native { git -C $closure add -- $expectedPaths } "Closure staging"

    $staged = @(git -C $closure diff --cached --name-only)
    Assert-ExactPaths $staged $expectedPaths "Staged closure"
    Run-Native { git -C $closure diff --cached --check } "Staged whitespace check"
    Run-Native { git -C $closure commit -m $commitSubject } "Closure commit"

    $closureCommit = (git -C $closure rev-parse HEAD).Trim()
    $closureParent = (git -C $closure rev-parse HEAD^).Trim()
    $closureSubject = (git -C $closure log -1 --format=%s).Trim()
    $committed = @(git -C $closure diff-tree --no-commit-id --name-only -r HEAD)

    if ($closureParent -ne $publishedMain) { throw "Closure parent mismatch." }
    if ($closureSubject -ne $commitSubject) { throw "Closure subject mismatch." }
    Assert-ExactPaths $committed $expectedPaths "Committed closure"

    if (@(git -C $closure status --short).Count -ne 0) {
        throw "Closure worktree is not clean after commit."
    }

    Write-Host "Governance-only closure commit: CREATED"

    Write-Host "`n=== STRICT FAST-FORWARD PUBLICATION ==="

    Run-Native { git -C $repo fetch origin main } "Pre-push fetch"

    if ((Get-RemoteMain $repo) -ne $publishedMain) { throw "Live remote main changed before closure push." }
    if ((git -C $repo rev-parse refs/remotes/origin/main).Trim() -ne $publishedMain) { throw "origin/main changed before closure push." }
    if ((git -C $repo rev-parse refs/heads/main).Trim() -ne $publishedMain) { throw "Local main changed before closure push." }

    Run-Native {
        git -C $closure merge-base --is-ancestor $publishedMain $closureCommit
    } "Fast-forward ancestry check"

    Run-Native {
        git -C $closure push --porcelain origin "${closureCommit}:refs/heads/main"
    } "Closure push"

    Run-Native { git -C $repo fetch origin main } "Post-push fetch"

    if ((Get-RemoteMain $repo) -ne $closureCommit) { throw "Live remote main does not match closure commit." }
    if ((git -C $repo rev-parse refs/remotes/origin/main).Trim() -ne $closureCommit) { throw "origin/main does not match closure commit." }

    if (@(git -C $repo worktree list --porcelain | Select-String -SimpleMatch "branch refs/heads/main").Count -ne 0) {
        throw "Local main became checked out before synchronization."
    }

    Run-Native { git -C $repo branch -f main $closureCommit } "Local main synchronization"

    Write-Host "`n=== FINAL PRESERVATION ==="

    if ((git -C $repo branch --show-current).Trim() -ne $originalBranch) { throw "Original branch changed." }
    if ((git -C $repo rev-parse HEAD).Trim() -ne $originalHead) { throw "Original HEAD changed." }
    if ((git -C $impl rev-parse HEAD).Trim() -ne $candidateCommit) { throw "Implementation candidate changed." }
    if ((git -C $gov rev-parse HEAD).Trim() -ne $reviewCommit) { throw "Governance review changed." }
    if ((git -C $integration rev-parse HEAD).Trim() -ne $publishedMain) { throw "Integration HEAD changed." }

    foreach ($worktree in @($repo, $impl, $gov, $integration, $closure)) {
        if (@(git -C $worktree status --short).Count -ne 0) {
            throw "Dirty worktree after closure: $worktree"
        }
    }

    $finalRemote = Get-RemoteMain $repo
    $finalTracking = (git -C $repo rev-parse refs/remotes/origin/main).Trim()
    $finalLocalMain = (git -C $repo rev-parse refs/heads/main).Trim()
    $finalClosureHead = (git -C $closure rev-parse HEAD).Trim()

    foreach ($sha in @($finalRemote, $finalTracking, $finalLocalMain, $finalClosureHead)) {
        if ($sha -ne $closureCommit) { throw "Final closure identity mismatch." }
    }

    Write-Host "`n=== WO-004 POST-PUBLICATION CLOSURE RESULT ==="

    [pscustomobject]@{
        PublishedImplementationHead = $publishedMain
        ClosureCommit = $closureCommit
        ClosureParent = $closureParent
        ClosureSubject = $closureSubject
        ClosurePathCount = $committed.Count
        LiveRemoteMain = $finalRemote
        OriginMain = $finalTracking
        LocalMain = $finalLocalMain
        ClosureWorktreeHead = $finalClosureHead
        GovernanceOnlyChange = $true
        PushType = "STRICT FAST-FORWARD"
        ForcePush = $false
        MergeCommit = $false
        TagCreated = $false
        ReleaseCreated = $false
        WorktreesClean = $true
        OriginalWorktreeUnchanged = $true
        FinalStatus = "WO-004 CLOSED"
    } | Format-List

    Write-Host "Closure paths:"
    $committed | ForEach-Object { Write-Host " - $_" }

    Write-Host "`nWO-004 POST-PUBLICATION CLOSURE: COMPLETE"
    Write-Host "Remote main, origin/main, local main, and closure HEAD are identical."
    Write-Host "No force-push, merge commit, tag, release, or cleanup was performed."
}
catch {
    if (Test-Path -LiteralPath $closure) {
        Write-Host "`nClosure worktree preserved for diagnosis:"
        git -C $closure status --short
    }
    throw
}
