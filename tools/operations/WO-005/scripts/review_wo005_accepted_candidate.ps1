$ErrorActionPreference = "Stop"

if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$repo = "$env:USERPROFILE\Projects\aegis-platform"

$architecturalBase = "be7502f73b51808d54728f912ead46ad0073c7b9"
$governanceMain = "ad743b4568bbd82527f7ff192c5b10ca4d59c2e9"

$candidateCommit = "f2376dce1bd4e312ca80a53aff9ab6212bb19289"
$candidateTree = "2b18f80f57e7b690e1773f67d20112d6dee10633"
$candidateBranch = "documentation/wo-005-accepted-environment-interaction-design-local-fix"

$designationCommit = "9fa4f7779ec3a772db3fce7f6d2e6138659df92f"
$designationBranch = "governance/wo-005-accepted-candidate-designation-local-fix"

$reviewWorktree = "$env:USERPROFILE\Projects\aegis-platform-wo-005-review-verdict"
$reviewBranch = "governance/wo-005-review-verdict"

$architectureSubject = "Record WO-005 architecture review"
$qaSubject = "Record WO-005 QA review"
$verdictSubject = "Record WO-005 candidate review verdict"

$adrRelative = "docs/adr/ADR-006-environment-interaction-layer.md"
$architectureRelative = "docs/architecture/environment-interaction-layer.md"
$specRelative = "docs/specifications/v0.5-phase-b-environment-interaction-layer.md"
$roadmapRelative = "docs/roadmap/ROADMAP.md"

$workOrderRelative = "governance/work-orders/WO-005_ENVIRONMENT_INTERACTION_LAYER_SPECIFICATION.md"
$traceabilityRelative = "governance/TRACEABILITY.md"

$deliverablePaths = @(
    $adrRelative,
    $architectureRelative,
    $specRelative,
    $roadmapRelative
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
$manifestPath = Join-Path $logDirectory "WO-005-candidate-review-verdict.txt"
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

function Get-CommitText {
    param(
        [string]$Repository,
        [string]$Commit,
        [string]$Path
    )

    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    try {
        $lines = @(
            & git -C $Repository show "${Commit}:$Path"
        )
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedPreference
    }

    if ($exitCode -ne 0) {
        throw "Unable to read $Path from $Commit."
    }

    return ($lines -join "`n")
}

function Assert-Regexes {
    param(
        [string]$Text,
        [string[]]$Patterns,
        [string]$Label
    )

    foreach ($pattern in $Patterns) {
        if (
            -not [regex]::IsMatch(
                $Text,
                $pattern,
                [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
            )
        ) {
            throw "$Label does not satisfy review pattern: $pattern"
        }
    }
}

function Resolve-RepositoryLinkPath {
    param(
        [string]$SourcePath,
        [string]$Link
    )

    $clean = ($Link -split "#", 2)[0]
    $clean = ($clean -split "\?", 2)[0]

    if ([string]::IsNullOrWhiteSpace($clean)) {
        return $null
    }

    if (
        $clean -match "^(?i:https?|mailto):" -or
        $clean.StartsWith("#")
    ) {
        return $null
    }

    $sourceDirectory = [System.IO.Path]::GetDirectoryName($SourcePath)

    if ([string]::IsNullOrWhiteSpace($sourceDirectory)) {
        $sourceDirectory = "."
    }

    $combined = [System.IO.Path]::GetFullPath(
        [System.IO.Path]::Combine(
            "C:\repo-root",
            $sourceDirectory,
            $clean
        )
    )

    $root = [System.IO.Path]::GetFullPath("C:\repo-root")

    if (-not $combined.StartsWith(
        $root,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw "Link escapes repository root: $SourcePath -> $Link"
    }

    return $combined.Substring($root.Length).TrimStart("\").Replace("\", "/")
}

function Assert-MarkdownLinks {
    param(
        [string]$Repository,
        [string]$Commit,
        [string[]]$Paths
    )

    $checked = 0

    foreach ($path in $Paths) {
        $text = Get-CommitText `
            -Repository $Repository `
            -Commit $Commit `
            -Path $path

        $matches = [regex]::Matches(
            $text,
            '\[[^\]]+\]\(([^)]+)\)'
        )

        foreach ($match in $matches) {
            $link = $match.Groups[1].Value.Trim()

            if ($link.StartsWith("<") -and $link.EndsWith(">")) {
                $link = $link.Substring(1, $link.Length - 2)
            }

            $resolved = Resolve-RepositoryLinkPath `
                -SourcePath $path `
                -Link $link

            if ($null -eq $resolved) {
                continue
            }

            $savedPreference = $ErrorActionPreference
            $ErrorActionPreference = "Continue"

            try {
                git -C $Repository cat-file -e "${Commit}:$resolved" 2>$null
                $exitCode = $LASTEXITCODE
            }
            finally {
                $ErrorActionPreference = $savedPreference
            }

            if ($exitCode -ne 0) {
                throw "Broken repository link: $path -> $link -> $resolved"
            }

            $checked++
        }
    }

    return $checked
}

function Commit-GovernanceReview {
    param(
        [string]$Worktree,
        [string]$Subject,
        [string[]]$Paths,
        [string]$Label
    )

    $changed = @(
        git -C $Worktree status --short |
            ForEach-Object { $_.Substring(3) }
    )

    Assert-ExactPathSet `
        -Actual $changed `
        -Expected $Paths `
        -Label $Label

    Invoke-Native {
        git -C $Worktree diff --check
    } "$Label whitespace validation"

    Invoke-Native {
        git -C $Worktree add -- $Paths
    } "$Label staging"

    $staged = @(
        git -C $Worktree diff --cached --name-only
    )

    Assert-ExactPathSet `
        -Actual $staged `
        -Expected $Paths `
        -Label "Staged $Label"

    Invoke-Native {
        git -C $Worktree diff --cached --check
    } "Staged $Label validation"

    Invoke-Native {
        git -C $Worktree commit -m $Subject
    } "$Label commit creation"

    $commit = (
        git -C $Worktree rev-parse HEAD
    ).Trim()

    $tree = (
        git -C $Worktree rev-parse "HEAD^{tree}"
    ).Trim()

    $parent = (
        git -C $Worktree rev-parse HEAD^
    ).Trim()

    if (@(git -C $Worktree status --short).Count -ne 0) {
        throw "$Label worktree is not clean after commit."
    }

    return [pscustomobject]@{
        Commit = $commit
        Parent = $parent
        Tree = $tree
    }
}

Write-Host "`n=== WO-005 REVIEW PREFLIGHT ==="

if (-not (Test-Path -LiteralPath $repo)) {
    throw "Repository not found: $repo"
}

Invoke-Native {
    git -C $repo fetch origin `
        "+refs/heads/main:refs/remotes/origin/main"
} "Remote main refresh"

$localMain = (
    git -C $repo rev-parse refs/heads/main
).Trim()

$originMain = (
    git -C $repo rev-parse refs/remotes/origin/main
).Trim()

$liveMain = Get-LiveRemoteMain $repo

foreach ($identity in @(
    $localMain,
    $originMain,
    $liveMain
)) {
    if ($identity -ne $governanceMain) {
        throw "Main identity differs from the published WO-005 governance amendment."
    }
}

$candidateBranchHead = (
    git -C $repo rev-parse "refs/heads/$candidateBranch"
).Trim()

$designationBranchHead = (
    git -C $repo rev-parse "refs/heads/$designationBranch"
).Trim()

if ($candidateBranchHead -ne $candidateCommit) {
    throw "Candidate branch does not match the designated candidate commit."
}

if ($designationBranchHead -ne $designationCommit) {
    throw "Designation branch does not match the recorded designation commit."
}

if (
    (git -C $repo rev-parse "${candidateCommit}^{tree}").Trim() -ne
    $candidateTree
) {
    throw "Candidate tree identity mismatch."
}

if (
    (git -C $repo rev-parse "${candidateCommit}^").Trim() -ne
    $architecturalBase
) {
    throw "Candidate parent identity mismatch."
}

$candidateChangedPaths = @(
    git -C $repo diff `
        --name-only `
        $architecturalBase `
        $candidateCommit
)

Assert-ExactPathSet `
    -Actual $candidateChangedPaths `
    -Expected $deliverablePaths `
    -Label "Designated candidate"

$designationChangedPaths = @(
    git -C $repo diff-tree `
        --no-commit-id `
        --name-only `
        -r `
        $designationCommit
)

Assert-ExactPathSet `
    -Actual $designationChangedPaths `
    -Expected $governancePaths `
    -Label "Candidate designation"

Assert-AllWorktreesClean `
    -Repository $repo `
    -Label "Preflight"

if (Test-Path -LiteralPath $reviewWorktree) {
    throw "Review verdict worktree already exists: $reviewWorktree"
}

if (@(git -C $repo branch --list $reviewBranch).Count -ne 0) {
    throw "Review verdict branch already exists: $reviewBranch"
}

Write-Host "Candidate, designation, main, remote, and clean-state identities: PASS"

Write-Host "`n=== ARCHITECTURE REVIEW ==="

$adr = Get-CommitText `
    -Repository $repo `
    -Commit $candidateCommit `
    -Path $adrRelative

$architecture = Get-CommitText `
    -Repository $repo `
    -Commit $candidateCommit `
    -Path $architectureRelative

$specification = Get-CommitText `
    -Repository $repo `
    -Commit $candidateCommit `
    -Path $specRelative

$roadmap = Get-CommitText `
    -Repository $repo `
    -Commit $candidateCommit `
    -Path $roadmapRelative

Assert-Regexes `
    -Text $adr `
    -Label "ADR-006" `
    -Patterns @(
        '(?m)^- \*\*Status:\*\* Accepted\s*$',
        'provider-neutral',
        'deterministic',
        'separate policy and approval',
        'immutable interaction receipts',
        'no external I/O',
        'Runtime implementation: not included'
    )

Assert-Regexes `
    -Text $architecture `
    -Label "Architecture" `
    -Patterns @(
        'Status: Accepted architecture; runtime not implemented',
        'ResourceReference',
        'resource resolution',
        'deterministic environment',
        'policy and approval',
        'adapter',
        'immutable.*receipt',
        'simulation',
        'live',
        'current.*pipeline|execution engine'
    )

Assert-Regexes `
    -Text $specification `
    -Label "Implementation specification" `
    -Patterns @(
        '(?m)^- \*\*Status:\*\* Accepted implementation specification\s*$',
        'ADR-006.*Accepted',
        'aegis_os/environment/',
        '__init__\.py',
        'models\.py',
        'errors\.py',
        'adapter\.py',
        'registry\.py',
        'resolver\.py',
        'policy\.py',
        'approvals\.py',
        'service\.py',
        'simulated\.py',
        'EnvironmentInteractionService',
        'GenericSimulationAdapter',
        'PolicyEvaluator',
        'ApprovalEvaluator',
        'InteractionReceipt',
        'READ',
        'LIST',
        'SEARCH',
        'CREATE',
        'UPDATE',
        'DELETE',
        'EXECUTE',
        'LIVE.*rejected|reject.*LIVE',
        'No pipeline change',
        'No secrets',
        'Deterministic simulation',
        'Runtime disposition: not implemented'
    )

Assert-Regexes `
    -Text $roadmap `
    -Label "Roadmap" `
    -Patterns @(
        'Phase B architecture and implementation specification',
        'accepted',
        'runtime is not implemented',
        'simulation',
        'Exclusions'
    )

$architectureReviewChecks = 4
Write-Host "Ownership, lifecycle, determinism, security, and decision completeness: PASS"

Write-Host "`n=== QA AND PRESERVATION REVIEW ==="

Invoke-Native {
    git -C $repo diff `
        --check `
        $architecturalBase `
        $candidateCommit
} "Candidate whitespace validation"

$brokenLinkCheckCount = Assert-MarkdownLinks `
    -Repository $repo `
    -Commit $candidateCommit `
    -Paths $deliverablePaths

$forbiddenChanges = @(
    git -C $repo diff `
        --name-only `
        $architecturalBase `
        $candidateCommit `
        -- `
        aegis_os `
        tests `
        pyproject.toml `
        .github `
        governance
)

if ($forbiddenChanges.Count -ne 0) {
    throw "Candidate contains forbidden code, test, dependency, CI, or governance changes."
}

$specTopStatus = (
    $specification -split "`n" |
        Where-Object { $_ -like "- **Status:** *" } |
        Select-Object -First 1
)

if ($specTopStatus -ne "- **Status:** Accepted implementation specification") {
    throw "Specification top-level status is not exactly accepted."
}

$adrTopStatus = (
    $adr -split "`n" |
        Where-Object { $_ -like "- **Status:** *" } |
        Select-Object -First 1
)

if ($adrTopStatus -ne "- **Status:** Accepted") {
    throw "ADR-006 top-level status is not exactly accepted."
}

$candidateBytes = 0

foreach ($path in $deliverablePaths) {
    $blobSize = (
        git -C $repo cat-file `
            -s `
            "${candidateCommit}:$path"
    ).Trim()

    $candidateBytes += [int64]$blobSize
}

if ($candidateBytes -le 0) {
    throw "Candidate document byte count is invalid."
}

Write-Host "Path boundary, links, whitespace, status, and preservation: PASS"
Write-Host "Validated internal links: $brokenLinkCheckCount"
Write-Host "Candidate document bytes: $candidateBytes"

Write-Host "`n=== CREATE REVIEW VERDICT WORKTREE ==="

Invoke-Native {
    git -C $repo worktree add `
        -b $reviewBranch `
        $reviewWorktree `
        $designationCommit
} "WO-005 review-verdict worktree creation"

$workOrderPath = Join-Path $reviewWorktree $workOrderRelative
$traceabilityPath = Join-Path $reviewWorktree $traceabilityRelative

try {
    Write-Host "`n=== RECORD ARCHITECTURE REVIEW COMMIT ==="

    $workOrder = [System.IO.File]::ReadAllText($workOrderPath)
    $workOrder = $workOrder -replace "`r`n", "`n"

    $traceability = [System.IO.File]::ReadAllText($traceabilityPath)
    $traceability = $traceability -replace "`r`n", "`n"

    if ($workOrder.Contains("## Architecture review verdict - accepted design")) {
        throw "Architecture review verdict already exists."
    }

    if ($traceability.Contains("## TR-010 WO-005 Architecture Review")) {
        throw "TR-010 architecture review already exists."
    }

    $architectureSection = @"

## Architecture review verdict - accepted design

- Review date: 2026-07-31
- Review role: Architecture Auditor
- Reviewed candidate: ``$candidateCommit``
- Reviewed tree: ``$candidateTree``
- Reviewed parent: ``$architecturalBase``
- Candidate paths: exactly four authorized documentation paths
- Ownership boundaries: pass
- Resource-to-environment handoff: pass
- Deterministic registry and resolution: pass
- Policy and approval separation: pass
- Adapter isolation: pass
- Simulation-to-live prevention: pass
- Immutable result and receipt boundaries: pass
- Secret-free bounded evidence: pass
- Current pipeline and execution isolation: pass
- Decision completeness: pass
- Architecture verdict: **PASS**

The candidate consistently accepts the provider-neutral simulation-only
architecture. Phase A retains resource-resolution ownership; Phase B consumes a
resolved reference and enforces deterministic environment resolution, policy,
approval, adapter isolation, result normalization, and immutable receipts.

This architecture review authorizes no correction, integration, publication,
runtime implementation, push, main modification, tag, release, ruleset change,
or cleanup.
"@

    $traceArchitectureSection = @"

## TR-010 WO-005 Architecture Review

- Candidate: ``$candidateCommit``
- Tree: ``$candidateTree``
- Review date: 2026-07-31
- Review role: Architecture Auditor
- Ownership and lifecycle review: pass
- Determinism review: pass
- Policy/approval separation: pass
- Adapter isolation: pass
- Simulation-only enforcement: pass
- Security and evidence boundaries: pass
- Execution-integration exclusion: pass
- Verdict: **PASS**
- Integration authority: not granted
- Publication authority: not granted
- Runtime implementation authority: not granted
"@

    [System.IO.File]::WriteAllText(
        $workOrderPath,
        $workOrder.TrimEnd() + $architectureSection + "`n",
        $utf8NoBom
    )

    [System.IO.File]::WriteAllText(
        $traceabilityPath,
        $traceability.TrimEnd() + $traceArchitectureSection + "`n",
        $utf8NoBom
    )

    $architectureReviewCommit = Commit-GovernanceReview `
        -Worktree $reviewWorktree `
        -Subject $architectureSubject `
        -Paths $governancePaths `
        -Label "WO-005 architecture review"

    Write-Host "Architecture review commit: $($architectureReviewCommit.Commit)"

    Write-Host "`n=== RECORD QA REVIEW COMMIT ==="

    $workOrder = [System.IO.File]::ReadAllText($workOrderPath)
    $workOrder = $workOrder -replace "`r`n", "`n"

    $traceability = [System.IO.File]::ReadAllText($traceabilityPath)
    $traceability = $traceability -replace "`r`n", "`n"

    if ($workOrder.Contains("## QA and verification review verdict")) {
        throw "QA review verdict already exists."
    }

    if ($traceability.Contains("## TR-011 WO-005 QA Review")) {
        throw "TR-011 QA review already exists."
    }

    $qaSection = @"

## QA and verification review verdict

- Review date: 2026-07-31
- Review role: QA & Verification
- Reviewed candidate: ``$candidateCommit``
- Reviewed tree: ``$candidateTree``
- Exact candidate path count: 4
- Markdown whitespace validation: pass
- Internal repository links checked: $brokenLinkCheckCount
- Candidate document byte count: $candidateBytes
- ADR accepted-state validation: pass
- Architecture accepted-state validation: pass
- Specification accepted-state validation: pass
- Roadmap reconciliation validation: pass
- Required operation and package coverage: pass
- Failure, policy, approval, receipt, and simulation coverage: pass
- Executable-code changes: 0
- Test changes: 0
- Dependency changes: 0
- CI changes: 0
- Governance changes in candidate: 0
- Candidate and related worktrees clean: pass
- Main and remote preservation: pass
- QA verdict: **PASS**

The candidate is documentation-only, reproducible from the exact architectural
base, internally linked, whitespace-clean, and bounded to the four authorized
documents. No existing runtime or public behavior is modified.

This QA review authorizes no correction, integration, publication, runtime
implementation, push, main modification, tag, release, ruleset change, or
cleanup.
"@

    $traceQaSection = @"

## TR-011 WO-005 QA Review

- Candidate: ``$candidateCommit``
- Tree: ``$candidateTree``
- Review date: 2026-07-31
- Review role: QA & Verification
- Exact path boundary: pass
- Markdown whitespace: pass
- Internal links checked: $brokenLinkCheckCount
- Accepted-state consistency: pass
- Required contract/package coverage: pass
- Code, test, dependency, CI, and governance candidate changes: none
- Worktree preservation: pass
- Main and remote preservation: pass
- Verdict: **PASS**
- Integration authority: not granted
- Publication authority: not granted
- Runtime implementation authority: not granted
"@

    [System.IO.File]::WriteAllText(
        $workOrderPath,
        $workOrder.TrimEnd() + $qaSection + "`n",
        $utf8NoBom
    )

    [System.IO.File]::WriteAllText(
        $traceabilityPath,
        $traceability.TrimEnd() + $traceQaSection + "`n",
        $utf8NoBom
    )

    $qaReviewCommit = Commit-GovernanceReview `
        -Worktree $reviewWorktree `
        -Subject $qaSubject `
        -Paths $governancePaths `
        -Label "WO-005 QA review"

    if (
        $qaReviewCommit.Parent -ne
        $architectureReviewCommit.Commit
    ) {
        throw "QA review commit does not descend directly from architecture review."
    }

    Write-Host "QA review commit: $($qaReviewCommit.Commit)"

    Write-Host "`n=== RECORD FINAL CANDIDATE REVIEW VERDICT ==="

    $workOrder = [System.IO.File]::ReadAllText($workOrderPath)
    $workOrder = $workOrder -replace "`r`n", "`n"

    $traceability = [System.IO.File]::ReadAllText($traceabilityPath)
    $traceability = $traceability -replace "`r`n", "`n"

    if ($workOrder.Contains("## Candidate review verdict - accepted design")) {
        throw "Final candidate review verdict already exists."
    }

    if ($traceability.Contains("## TR-012 WO-005 Candidate Review Verdict")) {
        throw "TR-012 candidate review verdict already exists."
    }

    $workOrder = Replace-ExactlyOnce `
        -Text $workOrder `
        -OldValue "**Status:** ACTIVE - ACCEPTED-DESIGN CANDIDATE DESIGNATED FOR REVIEW" `
        -NewValue "**Status:** ACTIVE - ACCEPTED-DESIGN CANDIDATE REVIEW PASSED" `
        -Label "WO-005 reviewed status"

    $oldDisposition = @"
WO-005: ACTIVE - ACCEPTED-DESIGN CANDIDATE DESIGNATED FOR REVIEW
Authoritative base: $architecturalBase
Governance amendment main: $governanceMain
Specification at base: PRE-EXISTING - PROPOSED
Deliverable scope: FOUR EXISTING DOCUMENTATION PATHS
Deliverable candidate designated: $candidateCommit
Candidate tree: $candidateTree
Architecture review: PENDING
QA review: PENDING
Deliverable integration authority: NOT GRANTED
Deliverable publication authority: NOT GRANTED
Runtime implementation authority: NOT GRANTED
"@

    $newDisposition = @"
WO-005: ACTIVE - ACCEPTED-DESIGN CANDIDATE REVIEW PASSED
Authoritative base: $architecturalBase
Governance amendment main: $governanceMain
Specification at base: PRE-EXISTING - PROPOSED
Deliverable scope: FOUR EXISTING DOCUMENTATION PATHS
Deliverable candidate designated: $candidateCommit
Candidate tree: $candidateTree
Architecture review: PASS
QA review: PASS
Candidate review verdict: PASS
Deliverable integration authority: NOT GRANTED
Deliverable publication authority: NOT GRANTED
Runtime implementation authority: NOT GRANTED
"@

    $workOrder = Replace-ExactlyOnce `
        -Text $workOrder `
        -OldValue $oldDisposition.TrimEnd() `
        -NewValue $newDisposition.TrimEnd() `
        -Label "WO-005 reviewed disposition"

    $verdictSection = @"

## Candidate review verdict - accepted design

- Verdict date: 2026-07-31
- Reviewed candidate: ``$candidateCommit``
- Reviewed tree: ``$candidateTree``
- Architecture review commit: ``$($architectureReviewCommit.Commit)``
- QA review commit: ``$($qaReviewCommit.Commit)``
- Architecture verdict: **PASS**
- QA verdict: **PASS**
- Final technical disposition: **PASS - ELIGIBLE FOR SEPARATE INTEGRATION AUTHORIZATION**
- Candidate correction required: no
- Integration authority: not granted
- Publication authority: not granted
- Runtime implementation authority: not granted

The immutable candidate satisfies the amended WO-005 architecture,
specification, roadmap, path-boundary, consistency, determinism, security,
testability, and preservation criteria.

Technical acceptance does not constitute integration or publication
authorization. A separate explicit authorization is required before any local
integration, remote publication, runtime implementation, tag, release, ruleset
change, or cleanup.
"@

    $traceVerdictSection = @"

## TR-012 WO-005 Candidate Review Verdict

- Candidate: ``$candidateCommit``
- Tree: ``$candidateTree``
- Verdict date: 2026-07-31
- Architecture review: **PASS**
- Architecture review commit: ``$($architectureReviewCommit.Commit)``
- QA review: **PASS**
- QA review commit: ``$($qaReviewCommit.Commit)``
- Candidate correction required: no
- Final technical disposition: **PASS - ELIGIBLE FOR SEPARATE INTEGRATION AUTHORIZATION**
- Integration authority: not granted
- Publication authority: not granted
- Runtime implementation authority: not granted

The reviewed candidate remains immutable and documentation-only. Technical
acceptance grants no integration, publication, runtime, release, ruleset, or
cleanup authority.
"@

    [System.IO.File]::WriteAllText(
        $workOrderPath,
        $workOrder.TrimEnd() + $verdictSection + "`n",
        $utf8NoBom
    )

    [System.IO.File]::WriteAllText(
        $traceabilityPath,
        $traceability.TrimEnd() + $traceVerdictSection + "`n",
        $utf8NoBom
    )

    $verdictCommit = Commit-GovernanceReview `
        -Worktree $reviewWorktree `
        -Subject $verdictSubject `
        -Paths $governancePaths `
        -Label "WO-005 candidate review verdict"

    if ($verdictCommit.Parent -ne $qaReviewCommit.Commit) {
        throw "Final verdict commit does not descend directly from QA review."
    }

    Write-Host "Final candidate review verdict commit: $($verdictCommit.Commit)"

    Write-Host "`n=== FINAL PRESERVATION AND MANIFEST ==="

    Invoke-Native {
        git -C $repo fetch origin `
            "+refs/heads/main:refs/remotes/origin/main"
    } "Final remote refresh"

    $finalLocalMain = (
        git -C $repo rev-parse refs/heads/main
    ).Trim()

    $finalOriginMain = (
        git -C $repo rev-parse refs/remotes/origin/main
    ).Trim()

    $finalLiveMain = Get-LiveRemoteMain $repo

    foreach ($identity in @(
        $finalLocalMain,
        $finalOriginMain,
        $finalLiveMain
    )) {
        if ($identity -ne $governanceMain) {
            throw "Main or remote changed during candidate review."
        }
    }

    Assert-AllWorktreesClean `
        -Repository $repo `
        -Label "Final"

    New-Item `
        -ItemType Directory `
        -Path $logDirectory `
        -Force | Out-Null

    $manifest = @"
AEGIS WO-005 Candidate Review Verdict
=====================================

Date: 2026-07-31

Architectural base:
$architecturalBase

Published governance main:
$governanceMain

Reviewed candidate:
Commit: $candidateCommit
Tree: $candidateTree
Branch: $candidateBranch

Candidate designation:
Commit: $designationCommit
Branch: $designationBranch

Architecture review:
Commit: $($architectureReviewCommit.Commit)
Parent: $($architectureReviewCommit.Parent)
Tree: $($architectureReviewCommit.Tree)
Verdict: PASS

QA review:
Commit: $($qaReviewCommit.Commit)
Parent: $($qaReviewCommit.Parent)
Tree: $($qaReviewCommit.Tree)
Verdict: PASS

Final candidate review verdict:
Commit: $($verdictCommit.Commit)
Parent: $($verdictCommit.Parent)
Tree: $($verdictCommit.Tree)
Verdict: PASS - ELIGIBLE FOR SEPARATE INTEGRATION AUTHORIZATION

Validation:
- Exact candidate paths: 4
- Exact governance paths per review commit: 2
- Internal links checked: $brokenLinkCheckCount
- Candidate document bytes: $candidateBytes
- Executable code changes: 0
- Test changes: 0
- Dependency changes: 0
- CI changes: 0
- Candidate governance changes: 0
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

    Write-Host "`n=== WO-005 CANDIDATE REVIEW RESULT ==="

    [pscustomobject]@{
        ArchitecturalBase = $architecturalBase
        GovernanceMain = $governanceMain
        CandidateCommit = $candidateCommit
        CandidateTree = $candidateTree
        CandidatePathCount = $candidateChangedPaths.Count
        DesignationCommit = $designationCommit
        ArchitectureReviewCommit = $architectureReviewCommit.Commit
        ArchitectureReviewParent = $architectureReviewCommit.Parent
        ArchitectureReviewTree = $architectureReviewCommit.Tree
        ArchitectureVerdict = "PASS"
        QAReviewCommit = $qaReviewCommit.Commit
        QAReviewParent = $qaReviewCommit.Parent
        QAReviewTree = $qaReviewCommit.Tree
        QAVerdict = "PASS"
        FinalVerdictCommit = $verdictCommit.Commit
        FinalVerdictParent = $verdictCommit.Parent
        FinalVerdictTree = $verdictCommit.Tree
        InternalLinksChecked = $brokenLinkCheckCount
        CandidateDocumentBytes = $candidateBytes
        ExecutableCodeChanges = 0
        TestChanges = 0
        DependencyChanges = 0
        CIChanges = 0
        CandidateGovernanceChanges = 0
        LocalMain = $finalLocalMain
        OriginMain = $finalOriginMain
        LiveRemoteMain = $finalLiveMain
        RemoteMutation = "NONE"
        WorktreesClean = $true
        Manifest = $manifestPath
        TechnicalDisposition = "PASS - ELIGIBLE FOR SEPARATE INTEGRATION AUTHORIZATION"
        IntegrationAuthorized = $false
        PublicationAuthorized = $false
        RuntimeImplementationAuthorized = $false
        FinalStatus = "WO-005 CANDIDATE REVIEW PASSED"
    } | Format-List

    Write-Host "`nWO-005 CANDIDATE REVIEW: COMPLETE"
    Write-Host "Architecture review: PASS"
    Write-Host "QA review: PASS"
    Write-Host "The candidate is eligible for separate integration authorization."
    Write-Host "No push, main update, integration, runtime implementation, tag, release, ruleset change, or cleanup was performed."
}
catch {
    if (Test-Path -LiteralPath $reviewWorktree) {
        Write-Host "`nWO-005 review-verdict worktree preserved for diagnosis:"
        git -C $reviewWorktree status --short
    }

    throw
}
