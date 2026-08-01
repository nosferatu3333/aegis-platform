$ErrorActionPreference = "Stop"

if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$repo = "$env:USERPROFILE\Projects\aegis-platform"
$worktree = "$env:USERPROFILE\Projects\aegis-platform-wo-006-enabling"
$branch = "governance/wo-006-enabling"

$base = "cfae92111eeb5355873a8c32c649514853564743"
$archiveCommit = "12486b34f46f82bd9103fa339a5cc0e849261bf6"
$archiveTree = "b07094cf696a913dee297bee86a26e36579ed6bf"
$candidate = "0bdd8ce58566c806136f1d85347d593fb7c27cbd"
$candidateTree = "d812753b1e563508100ad21d815fb02ae99f974f"

$specPath = "docs/specifications/v0.5-phase-b-environment-interaction-layer.md"
$adrPath = "docs/adr/ADR-006-environment-interaction-layer.md"
$tracePath = "governance/TRACEABILITY.md"
$workOrderPath = "governance/work-orders/WO-006_ENVIRONMENT_INTERACTION_LAYER_SIMULATION_RUNTIME.md"

$expectedCandidatePaths = @(
    $specPath,
    $tracePath,
    $workOrderPath
)

$operationsRoot = [Environment]::GetEnvironmentVariable(
    "AEGIS_OPERATIONS",
    "User"
)

if ([string]::IsNullOrWhiteSpace($operationsRoot)) {
    $operationsRoot = "$env:USERPROFILE\Projects\AEGIS-operations"
}

$logDirectory = Join-Path $operationsRoot "logs\WO-006"
$reportPath = Join-Path $logDirectory "WO-006-enabling-independent-review.txt"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

$blocking = New-Object System.Collections.Generic.List[string]
$findings = New-Object System.Collections.Generic.List[string]
$evidence = New-Object System.Collections.Generic.List[string]

function Invoke-Native {
    param(
        [scriptblock]$Command,
        [string]$Label,
        [switch]$AllowFailure
    )

    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    try {
        $output = @(& $Command 2>&1)
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedPreference
    }

    if (-not $AllowFailure -and $exitCode -ne 0) {
        throw "$Label failed with exit code $exitCode.`n$($output -join [Environment]::NewLine)"
    }

    return [pscustomobject]@{
        Output = $output
        ExitCode = $exitCode
    }
}

function Get-SingleLine {
    param(
        [scriptblock]$Command,
        [string]$Label
    )

    $result = Invoke-Native $Command $Label

    if ($result.Output.Count -ne 1) {
        throw "$Label returned $($result.Output.Count) lines; expected exactly one."
    }

    return ([string]$result.Output[0]).Trim()
}

function Get-LiveRemoteMain {
    param([string]$Repository)

    $result = Invoke-Native {
        git -C $Repository ls-remote --heads origin refs/heads/main
    } "Live remote main lookup"

    if ($result.Output.Count -ne 1) {
        throw "Expected exactly one live remote main reference."
    }

    return (([string]$result.Output[0] -split "\s+")[0]).Trim()
}

function Get-CommitText {
    param(
        [string]$Repository,
        [string]$Commit,
        [string]$Path
    )

    $spec = "${Commit}:$Path"

    $result = Invoke-Native {
        git -C $Repository show $spec
    } "Read $Path at $Commit"

    return (($result.Output | ForEach-Object { [string]$_ }) -join "`n")
}

function Get-CommitPaths {
    param(
        [string]$Repository,
        [string]$Commit
    )

    $result = Invoke-Native {
        git -C $Repository diff-tree `
            --no-commit-id `
            --name-only `
            -r `
            $Commit
    } "Read commit paths for $Commit"

    return @(
        $result.Output |
            ForEach-Object { ([string]$_).Trim() } |
            Where-Object { $_ } |
            Sort-Object -Unique
    )
}

function Assert-Equal {
    param(
        [string]$Actual,
        [string]$Expected,
        [string]$Code,
        [string]$Description
    )

    if ($Actual -ne $Expected) {
        $blocking.Add("$Code — $Description. Expected '$Expected'; found '$Actual'.")
    }
    else {
        $evidence.Add("$Code — PASS — ${Description}: $Actual")
    }
}

function Assert-True {
    param(
        [bool]$Condition,
        [string]$Code,
        [string]$Description
    )

    if (-not $Condition) {
        $blocking.Add("$Code — $Description.")
    }
    else {
        $evidence.Add("$Code — PASS — $Description")
    }
}

function Assert-Contains {
    param(
        [string]$Text,
        [string]$Expected,
        [string]$Code,
        [string]$Description
    )

    if (-not $Text.Contains($Expected)) {
        $blocking.Add("$Code — Missing required text: $Description.")
    }
    else {
        $evidence.Add("$Code — PASS — $Description")
    }
}

function Assert-NotContains {
    param(
        [string]$Text,
        [string]$Forbidden,
        [string]$Code,
        [string]$Description
    )

    if ($Text.Contains($Forbidden)) {
        $blocking.Add("$Code — Forbidden stale text remains: $Description.")
    }
    else {
        $evidence.Add("$Code — PASS — $Description absent")
    }
}

function Assert-ExactPathSet {
    param(
        [string[]]$Actual,
        [string[]]$Expected,
        [string]$Code,
        [string]$Description
    )

    $actualSorted = @($Actual | Sort-Object -Unique)
    $expectedSorted = @($Expected | Sort-Object -Unique)

    $missing = @(
        $expectedSorted |
            Where-Object { $_ -notin $actualSorted }
    )

    $unexpected = @(
        $actualSorted |
            Where-Object { $_ -notin $expectedSorted }
    )

    if (
        $actualSorted.Count -ne $expectedSorted.Count -or
        $missing.Count -gt 0 -or
        $unexpected.Count -gt 0
    ) {
        $blocking.Add(
            "$Code — $Description. " +
            "Missing=[$($missing -join ', ')]; " +
            "Unexpected=[$($unexpected -join ', ')]."
        )
    }
    else {
        $evidence.Add(
            "$Code — PASS — ${Description}: " +
            ($actualSorted -join ", ")
        )
    }
}

Write-Host "`n=== WO-006 ENABLING INDEPENDENT REVIEW ==="

if (-not (Test-Path -LiteralPath $repo)) {
    throw "Repository not found: $repo"
}

if (-not (Test-Path -LiteralPath $worktree)) {
    throw "WO-006 enabling worktree not found: $worktree"
}

Write-Host "Reviewing local candidate without mutation..."

# Identity and preservation checks
$currentBranch = Get-SingleLine {
    git -C $worktree branch --show-current
} "Current enabling branch"

$currentHead = Get-SingleLine {
    git -C $worktree rev-parse HEAD
} "Current enabling HEAD"

$currentTree = Get-SingleLine {
    git -C $worktree rev-parse "HEAD^{tree}"
} "Current enabling tree"

$localMain = Get-SingleLine {
    git -C $repo rev-parse refs/heads/main
} "Local main"

$originMain = Get-SingleLine {
    git -C $repo rev-parse refs/remotes/origin/main
} "Remote-tracking main"

$liveMain = Get-LiveRemoteMain $repo

Assert-Equal $currentBranch $branch "ID-001" "Enabling branch"
Assert-Equal $currentHead $candidate "ID-002" "Enabling worktree HEAD"
Assert-Equal $currentTree $candidateTree "ID-003" "Enabling candidate tree"
Assert-Equal $localMain $base "ID-004" "Local main preservation"
Assert-Equal $originMain $base "ID-005" "origin/main preservation"
Assert-Equal $liveMain $base "ID-006" "Live remote main preservation"

$worktreeStatus = @(
    git -C $worktree status --short
)

Assert-True `
    ($worktreeStatus.Count -eq 0) `
    "ID-007" `
    "Enabling worktree is clean"

# Commit lineage checks
$archiveParent = Get-SingleLine {
    git -C $repo rev-parse "$archiveCommit^"
} "Archive parent"

$actualArchiveTree = Get-SingleLine {
    git -C $repo rev-parse "$archiveCommit^{tree}"
} "Archive tree"

$candidateParent = Get-SingleLine {
    git -C $repo rev-parse "$candidate^"
} "Candidate parent"

$archiveSubject = Get-SingleLine {
    git -C $repo log -1 --format=%s $archiveCommit
} "Archive subject"

$candidateSubject = Get-SingleLine {
    git -C $repo log -1 --format=%s $candidate
} "Candidate subject"

$commitCount = [int](Get-SingleLine {
    git -C $repo rev-list --count "$base..$candidate"
} "Local commit count")

$mergeCommits = @(
    git -C $repo rev-list --merges "$base..$candidate"
)

Assert-Equal $archiveParent $base "LIN-001" "Archive parent"
Assert-Equal $actualArchiveTree $archiveTree "LIN-002" "Archive tree"
Assert-Equal $candidateParent $archiveCommit "LIN-003" "Candidate parent"
Assert-Equal $archiveSubject "Archive operational scripts before WO-006 enabling" "LIN-004" "Archive subject"
Assert-Equal $candidateSubject "Record WO-006 enabling boundary" "LIN-005" "Candidate subject"
Assert-True ($commitCount -eq 2) "LIN-006" "Exactly two commits descend from the closed WO-005 base"
Assert-True ($mergeCommits.Count -eq 0) "LIN-007" "No merge commit exists in the enabling lineage"

# Path-boundary checks
$archivePaths = @(Get-CommitPaths $repo $archiveCommit)
$candidatePaths = @(Get-CommitPaths $repo $candidate)

$archiveEscapes = @(
    $archivePaths |
        Where-Object { $_ -notlike "tools/operations/*" }
)

Assert-True ($archivePaths.Count -eq 29) "PATH-001" "Archive commit contains exactly 29 paths"
Assert-True ($archiveEscapes.Count -eq 0) "PATH-002" "Archive commit is limited to tools/operations/**"
Assert-ExactPathSet `
    -Actual $candidatePaths `
    -Expected $expectedCandidatePaths `
    -Code "PATH-003" `
    -Description "Enabling commit exact path boundary"

$technicalPaths = @(
    git -C $repo diff `
        --name-only `
        $base `
        $candidate `
        -- `
        aegis_os `
        tests `
        benchmarks `
        pyproject.toml `
        .github
)

Assert-True `
    ($technicalPaths.Count -eq 0) `
    "PATH-004" `
    "No runtime, test, benchmark, dependency, or CI path changed"

# ADR preservation checks
$baseAdrBlob = Get-SingleLine {
    git -C $repo rev-parse "${base}:$adrPath"
} "Base ADR-006 blob"

$candidateAdrBlob = Get-SingleLine {
    git -C $repo rev-parse "${candidate}:$adrPath"
} "Candidate ADR-006 blob"

$adrText = Get-CommitText $repo $candidate $adrPath

Assert-Equal $candidateAdrBlob $baseAdrBlob "ADR-001" "ADR-006 blob remains unchanged"
Assert-Contains $adrText "Status: Accepted" "ADR-002" "ADR-006 remains Accepted"

# Specification checks
$specText = Get-CommitText $repo $candidate $specPath

Assert-Contains `
    $specText `
    "14. ADR-006 accepted-state verification." `
    "SPEC-001" `
    "Implementation order uses accepted-state verification"

Assert-Contains `
    $specText `
    "## 47. ADR-006 accepted-state preservation" `
    "SPEC-002" `
    "Section 47 is an accepted-state preservation section"

Assert-Contains `
    $specText `
    "ADR-006 is already Accepted through the completed WO-005 architecture review" `
    "SPEC-003" `
    "Section 47 recognizes the completed WO-005 acceptance"

Assert-Contains `
    $specText `
    "| ADR-006 | Remains Accepted during runtime implementation and verification |" `
    "SPEC-004" `
    "Decision table preserves Accepted status"

Assert-Contains `
    $specText `
    "## WO-006 enabling correction" `
    "SPEC-005" `
    "Bounded enabling correction is recorded"

Assert-Contains `
    $specText `
    "Runtime implementation authority granted by this correction: no" `
    "SPEC-006" `
    "Specification correction grants no runtime authority"

Assert-NotContains `
    $specText `
    "ADR-006 may move from Proposed to Accepted only after" `
    "SPEC-007" `
    "Old Proposed-to-Accepted transition"

Assert-NotContains `
    $specText `
    "| ADR-006 | Remains Proposed until runtime acceptance evidence |" `
    "SPEC-008" `
    "Old decision-table Proposed status"

Assert-NotContains `
    $specText `
    "14. ADR-006 review." `
    "SPEC-009" `
    "Old ambiguous implementation-order review step"

# Work-order checks
$workOrderText = Get-CommitText $repo $candidate $workOrderPath

Assert-Contains `
    $workOrderText `
    "**Status:** ENABLING - LOCAL GOVERNANCE CANDIDATE; ACTIVATION NOT GRANTED" `
    "WO-001" `
    "WO-006 status remains enabling-only"

Assert-Contains `
    $workOrderText `
    "**Runtime implementation authority:** NOT GRANTED" `
    "WO-002" `
    "Runtime implementation remains unauthorized"

Assert-Contains `
    $workOrderText `
    "**Benchmark implementation authority:** NOT GRANTED" `
    "WO-003" `
    "Benchmark implementation remains unauthorized"

Assert-Contains `
    $workOrderText `
    "**Remote-publication authority:** NOT GRANTED" `
    "WO-004" `
    "Remote publication remains unauthorized"

Assert-Contains `
    $workOrderText `
    "Next required action: INDEPENDENT REVIEW AND SEPARATE ACTIVATION DECISION" `
    "WO-005" `
    "Next gate is review and separate activation"

$runtimeAllowlist = @(
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

$testAllowlist = @(
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

foreach ($path in $runtimeAllowlist) {
    Assert-Contains `
        $workOrderText `
        "``$path``" `
        "WO-RUNTIME" `
        "Runtime allowlist contains $path"
}

foreach ($path in $testAllowlist) {
    Assert-Contains `
        $workOrderText `
        "``$path``" `
        "WO-TEST" `
        "Focused-test allowlist contains $path"
}

# Traceability checks
$traceText = Get-CommitText $repo $candidate $tracePath

Assert-Contains `
    $traceText `
    "## TR-014 WO-006 Enabling Boundary" `
    "TR-001" `
    "TR-014 enabling record exists"

Assert-Contains `
    $traceText `
    "- Parent local operations-archive commit: ``$archiveCommit``" `
    "TR-002" `
    "TR-014 records the archive parent"

Assert-Contains `
    $traceText `
    "- ADR-006 authoritative state: **ACCEPTED**" `
    "TR-003" `
    "TR-014 preserves ADR-006 Accepted state"

Assert-Contains `
    $traceText `
    "- Current disposition: **LOCAL ENABLING CANDIDATE - REVIEW REQUIRED**" `
    "TR-004" `
    "TR-014 records review-required disposition"

# Operational-archive hygiene scan
$secretPatterns = @(
    'sk-[A-Za-z0-9]{20,}',
    'ghp_[A-Za-z0-9]{20,}',
    'github_pat_[A-Za-z0-9_]{20,}',
    'AKIA[0-9A-Z]{16}',
    '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'Authorization:\s*Bearer\s+[A-Za-z0-9._-]+'
)

foreach ($pattern in $secretPatterns) {
    $scan = Invoke-Native {
        git -C $repo grep -n -I -E $pattern $archiveCommit -- tools/operations
    } "Secret scan pattern $pattern" -AllowFailure

    if ($scan.ExitCode -eq 0 -and $scan.Output.Count -gt 0) {
        $blocking.Add(
            "SEC-001 — Potential credential material detected for pattern '$pattern': " +
            (($scan.Output | Select-Object -First 5) -join " | ")
        )
    }
}

if (-not ($blocking | Where-Object { $_ -like "SEC-001*" })) {
    $evidence.Add("SEC-001 — PASS — No common credential pattern detected in the archived operational files")
}

$localPathScan = Invoke-Native {
    git -C $repo grep -n -I -F "$env:USERPROFILE" $archiveCommit -- tools/operations
} "Local path scan" -AllowFailure

if ($localPathScan.ExitCode -eq 0 -and $localPathScan.Output.Count -gt 0) {
    $findings.Add(
        "ARCH-001 — The public-candidate archive contains local absolute paths " +
        "for $env:USERPROFILE in $($localPathScan.Output.Count) matching lines. " +
        "This is operationally expected but should be explicitly accepted before publication."
    )
}
else {
    $evidence.Add("ARCH-001 — PASS — No local absolute user path detected")
}

$mojibakePatterns = @("ÔÇ", "Ã", "â€", "ï»¿")

foreach ($pattern in $mojibakePatterns) {
    $scan = Invoke-Native {
        git -C $repo grep -n -I -F $pattern $archiveCommit -- tools/operations
    } "Mojibake scan $pattern" -AllowFailure

    if ($scan.ExitCode -eq 0 -and $scan.Output.Count -gt 0) {
        $findings.Add(
            "ARCH-002 — Possible mojibake sequence '$pattern' appears in archived content: " +
            (($scan.Output | Select-Object -First 5) -join " | ")
        )
    }
}

$archiveWhitespace = Invoke-Native {
    git -C $repo diff --check "$base..$archiveCommit"
} "Historical archive whitespace scan" -AllowFailure

if ($archiveWhitespace.ExitCode -ne 0) {
    $findings.Add(
        "ARCH-003 — Historical operational scripts contain whitespace findings. " +
        "They are preserved archive evidence and do not affect runtime or governance semantics. " +
        "Finding count shown by Git: $($archiveWhitespace.Output.Count)."
    )
}
else {
    $evidence.Add("ARCH-003 — PASS — No archive whitespace finding")
}

# Final verdict
$architecturePass = (
    $blocking.Count -eq 0 -and
    $technicalPaths.Count -eq 0 -and
    $candidateAdrBlob -eq $baseAdrBlob
)

$governancePass = (
    $blocking.Count -eq 0 -and
    $candidatePaths.Count -eq 3
)

$publicationEligibility = if ($blocking.Count -eq 0) {
    "ELIGIBLE FOR SEPARATE PUBLICATION AUTHORIZATION"
}
else {
    "BLOCKED"
}

$runtimeEligibility = "NOT AUTHORIZED — SEPARATE ACTIVATION AND BENCHMARK-PATH DECISION REQUIRED"

New-Item `
    -ItemType Directory `
    -Path $logDirectory `
    -Force | Out-Null

$reportLines = New-Object System.Collections.Generic.List[string]

$reportLines.Add("AEGIS WO-006 Enabling Independent Review")
$reportLines.Add("========================================")
$reportLines.Add("")
$reportLines.Add("Review date: 2026-08-01")
$reportLines.Add("Authoritative base: $base")
$reportLines.Add("Archive commit: $archiveCommit")
$reportLines.Add("Archive tree: $archiveTree")
$reportLines.Add("Enabling candidate: $candidate")
$reportLines.Add("Enabling tree: $candidateTree")
$reportLines.Add("Branch: $branch")
$reportLines.Add("Worktree: $worktree")
$reportLines.Add("")
$reportLines.Add("Architecture review: $(if ($architecturePass) { 'PASS' } else { 'FAIL' })")
$reportLines.Add("Governance review: $(if ($governancePass) { 'PASS' } else { 'FAIL' })")
$reportLines.Add("Publication eligibility: $publicationEligibility")
$reportLines.Add("Runtime implementation: $runtimeEligibility")
$reportLines.Add("")
$reportLines.Add("Blocking issues:")
if ($blocking.Count -eq 0) {
    $reportLines.Add("- NONE")
}
else {
    foreach ($item in $blocking) {
        $reportLines.Add("- $item")
    }
}

$reportLines.Add("")
$reportLines.Add("Non-blocking findings:")
if ($findings.Count -eq 0) {
    $reportLines.Add("- NONE")
}
else {
    foreach ($item in $findings) {
        $reportLines.Add("- $item")
    }
}

$reportLines.Add("")
$reportLines.Add("Verification evidence:")
foreach ($item in $evidence) {
    $reportLines.Add("- $item")
}

$reportLines.Add("")
$reportLines.Add("Preservation:")
$reportLines.Add("- Local main: $localMain")
$reportLines.Add("- origin/main: $originMain")
$reportLines.Add("- Live remote main: $liveMain")
$reportLines.Add("- Fetch performed: NO")
$reportLines.Add("- Commit created: NO")
$reportLines.Add("- Push performed: NO")
$reportLines.Add("- Tag or release changed: NO")
$reportLines.Add("- Ruleset changed: NO")
$reportLines.Add("- Worktree cleanup performed: NO")
$reportLines.Add("")
$reportLines.Add("Final disposition: $publicationEligibility")

[System.IO.File]::WriteAllLines(
    $reportPath,
    $reportLines,
    $utf8NoBom
)

Write-Host "`n=== WO-006 ENABLING REVIEW RESULT ==="

[pscustomobject]@{
    AuthoritativeBase = $base
    ArchiveCommit = $archiveCommit
    ArchiveTree = $archiveTree
    EnablingCandidate = $candidate
    EnablingTree = $candidateTree
    Branch = $branch
    ArchitectureReview = if ($architecturePass) { "PASS" } else { "FAIL" }
    GovernanceReview = if ($governancePass) { "PASS" } else { "FAIL" }
    BlockingIssueCount = $blocking.Count
    NonBlockingFindingCount = $findings.Count
    PublicationEligibility = $publicationEligibility
    RuntimeImplementationAuthorized = $false
    BenchmarkImplementationAuthorized = $false
    LocalMain = $localMain
    OriginMain = $originMain
    LiveRemoteMain = $liveMain
    FetchPerformed = $false
    CommitCreated = $false
    PushPerformed = $false
    RulesetChanged = $false
    WorktreeCleanupPerformed = $false
    Report = $reportPath
} | Format-List

Write-Host "Blocking issues:"
if ($blocking.Count -eq 0) {
    Write-Host " - NONE"
}
else {
    $blocking | ForEach-Object { Write-Host " - $_" }
}

Write-Host "Non-blocking findings:"
if ($findings.Count -eq 0) {
    Write-Host " - NONE"
}
else {
    $findings | ForEach-Object { Write-Host " - $_" }
}

Write-Host "`nWO-006 ENABLING REVIEW: COMPLETE"
Write-Host "No repository or remote mutation was performed."
