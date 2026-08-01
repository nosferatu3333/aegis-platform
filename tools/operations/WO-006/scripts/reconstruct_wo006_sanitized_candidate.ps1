$ErrorActionPreference = "Stop"

if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$repo = "$env:USERPROFILE\Projects\aegis-platform"
$sourceOperations = Join-Path $repo "tools\operations"

$originalWorktree = "$env:USERPROFILE\Projects\aegis-platform-wo-006-enabling"
$originalBranch = "governance/wo-006-enabling"
$originalArchive = "12486b34f46f82bd9103fa339a5cc0e849261bf6"
$originalCandidate = "0bdd8ce58566c806136f1d85347d593fb7c27cbd"
$originalCandidateTree = "d812753b1e563508100ad21d815fb02ae99f974f"

$sanitizedWorktree = "$env:USERPROFILE\Projects\aegis-platform-wo-006-enabling-sanitized"
$sanitizedBranch = "governance/wo-006-enabling-sanitized"

$base = "cfae92111eeb5355873a8c32c649514853564743"
$archiveSubject = "Archive sanitized operational scripts before WO-006 enabling"
$enablingSubject = "Record sanitized WO-006 enabling boundary"

$specRelative = "docs/specifications/v0.5-phase-b-environment-interaction-layer.md"
$traceRelative = "governance/TRACEABILITY.md"
$workOrderRelative = "governance/work-orders/WO-006_ENVIRONMENT_INTERACTION_LAYER_SIMULATION_RUNTIME.md"

$governancePaths = @(
    $specRelative,
    $traceRelative,
    $workOrderRelative
)

$operationsRoot = [Environment]::GetEnvironmentVariable(
    "AEGIS_OPERATIONS",
    "User"
)

if ([string]::IsNullOrWhiteSpace($operationsRoot)) {
    $operationsRoot = "$env:USERPROFILE\Projects\AEGIS-operations"
}

$logDirectory = Join-Path $operationsRoot "logs\WO-006"
$manifestPath = Join-Path $logDirectory "WO-006-sanitized-enabling-local-commits.txt"

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

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

function Get-RemoteSnapshot {
    param([string]$Repository)

    $result = Invoke-Native {
        git -C $Repository ls-remote --heads --tags origin
    } "Remote reference snapshot"

    return @(
        $result.Output |
            ForEach-Object { ([string]$_).Trim() } |
            Where-Object { $_ } |
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
            throw "$Label changed."
        }
    }
}

function Normalize-PathText {
    param([string]$Path)

    return ([System.IO.Path]::GetFullPath($Path)).
        Replace([char]92, [char]47).
        TrimEnd([char]47).
        ToLowerInvariant()
}

function Get-WorktreePaths {
    param([string]$Repository)

    return @(
        git -C $Repository worktree list --porcelain |
            Where-Object { $_ -like "worktree *" } |
            ForEach-Object { $_.Substring(9) }
    )
}

function Assert-OtherWorktreesClean {
    param(
        [string]$Repository,
        [string[]]$AllowedDirty
    )

    $allowed = @(
        $AllowedDirty |
            ForEach-Object { Normalize-PathText $_ }
    )

    foreach ($path in @(Get-WorktreePaths $Repository)) {
        if ((Normalize-PathText $path) -in $allowed) {
            continue
        }

        if (@(git -C $path status --short).Count -ne 0) {
            throw "Unexpected dirty worktree: $path"
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
        throw (
            "$Label mismatch. Missing=[$($missing -join ', ')]; " +
            "Unexpected=[$($unexpected -join ', ')]."
        )
    }
}

function Read-CommitFile {
    param(
        [string]$Repository,
        [string]$Commit,
        [string]$Path
    )

    $gitObject = "${Commit}:$Path"

    $result = Invoke-Native {
        git -C $Repository show $gitObject
    } "Read $Path from $Commit"

    return (($result.Output | ForEach-Object { [string]$_ }) -join "`n")
}

function Write-Utf8NoBom {
    param(
        [string]$Path,
        [string]$Content
    )

    $parent = Split-Path -Parent $Path

    if ($parent) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    [System.IO.File]::WriteAllText(
        $Path,
        $Content,
        $utf8NoBom
    )
}

function Copy-DirectoryContents {
    param(
        [string]$Source,
        [string]$Destination
    )

    New-Item -ItemType Directory -Path $Destination -Force | Out-Null

    Get-ChildItem -LiteralPath $Source -Force |
        Copy-Item -Destination $Destination -Recurse -Force
}

function Sanitize-OperationsArchive {
    param([string]$OperationsDirectory)

    $textExtensions = @(
        ".ps1", ".md", ".csv", ".txt", ".json",
        ".yaml", ".yml", ".toml", ".html", ".js"
    )

    $changedFiles = New-Object System.Collections.Generic.List[string]

    foreach ($file in @(
        Get-ChildItem -LiteralPath $OperationsDirectory -Recurse -File -Force
    )) {
        if ($file.Extension.ToLowerInvariant() -notin $textExtensions) {
            continue
        }

        $text = [System.IO.File]::ReadAllText($file.FullName)
        $original = $text

        if ($file.Extension.ToLowerInvariant() -eq ".ps1") {
            $text = $text.Replace(
                "$env:USERPROFILE",
                '$env:USERPROFILE'
            )

            $text = $text.Replace(
                "$env:USERPROFILE",
                '$env:USERPROFILE'
            )

            $text = $text.Replace(
                "$env:USERPROFILE",
                '$env:USERPROFILE'
            )
        }
        else {
            $text = $text.Replace(
                "$env:USERPROFILE",
                "<USER_PROFILE>"
            )

            $text = $text.Replace(
                "$env:USERPROFILE",
                "<USER_PROFILE>"
            )

            $text = $text.Replace(
                "$env:USERPROFILE",
                "<USER_PROFILE>"
            )
        }

        $text = $text.Replace(
            "<LOCAL_USER>",
            "<LOCAL_USER>"
        )

        if ($text -ne $original) {
            [System.IO.File]::WriteAllText(
                $file.FullName,
                $text,
                $utf8NoBom
            )

            $relative = $file.FullName.Substring(
                $OperationsDirectory.Length
            ).TrimStart("\", "/")

            $changedFiles.Add($relative)
        }
    }

    return @($changedFiles)
}

function Update-ScriptInventory {
    param([string]$OperationsDirectory)

    $inventoryPath = Join-Path `
        $OperationsDirectory `
        "SCRIPT_INVENTORY_2026-07-31.csv"

    if (-not (Test-Path -LiteralPath $inventoryPath)) {
        return
    }

    $rows = @(Import-Csv -LiteralPath $inventoryPath)

    if ($rows.Count -eq 0) {
        return
    }

    $columns = @($rows[0].PSObject.Properties.Name)

    $destinationCandidates = @(
        "DestinationPath",
        "Destination Path",
        "ArchivePath",
        "Archive Path",
        "RepositoryPath",
        "Repository Path",
        "Destination",
        "TargetPath",
        "Target Path",
        "Target",
        "ArchivedPath"
    )

    $hashCandidates = @(
        "SHA256",
        "SHA-256",
        "Sha256",
        "Hash",
        "FileHash",
        "File Hash",
        "Checksum"
    )

    $statusCandidates = @(
        "Status",
        "Disposition",
        "Result",
        "Action"
    )

    $destinationColumn = $destinationCandidates |
        Where-Object { $_ -in $columns } |
        Select-Object -First 1

    $hashColumn = $hashCandidates |
        Where-Object { $_ -in $columns } |
        Select-Object -First 1

    $statusColumn = $statusCandidates |
        Where-Object { $_ -in $columns } |
        Select-Object -First 1

    if (-not $destinationColumn -and $columns.Count -ge 4) {
        $destinationColumn = $columns[3]
    }

    if (-not $hashColumn -and $columns.Count -ge 5) {
        $hashColumn = $columns[4]
    }

    if (-not $statusColumn -and $columns.Count -ge 6) {
        $statusColumn = $columns[5]
    }

    if (-not $destinationColumn -or -not $hashColumn) {
        throw "Inventory columns could not be resolved. Headers: $($columns -join ', ')"
    }

    foreach ($row in $rows) {
        $repositoryPath = [string](
            $row.PSObject.Properties[$destinationColumn].Value
        )

        $normalized = $repositoryPath.Replace("/", "\")
        $prefix = "tools\operations\"

        if ($normalized.StartsWith(
            $prefix,
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
            $relative = $normalized.Substring($prefix.Length)
        }
        else {
            $relative = $normalized
        }

        $target = Join-Path $OperationsDirectory $relative

        if (Test-Path -LiteralPath $target) {
            $row.PSObject.Properties[$hashColumn].Value = (
                Get-FileHash `
                    -LiteralPath $target `
                    -Algorithm SHA256
            ).Hash.ToLowerInvariant()

            if ($statusColumn) {
                $status = [string](
                    $row.PSObject.Properties[$statusColumn].Value
                )

                if ($status -notmatch "SANITIZED PUBLIC COPY") {
                    $row.PSObject.Properties[$statusColumn].Value = (
                        "$status; SANITIZED PUBLIC COPY"
                    ).TrimStart([char[]]"; ")
                }
            }
        }
    }

    $csvLines = @($rows | ConvertTo-Csv -NoTypeInformation)

    [System.IO.File]::WriteAllLines(
        $inventoryPath,
        $csvLines,
        $utf8NoBom
    )
}

function Regenerate-HashManifests {
    param([string]$OperationsDirectory)

    foreach ($manifest in @(
        Get-ChildItem `
            -LiteralPath $OperationsDirectory `
            -Recurse `
            -File `
            -Filter "SHA256SUMS.txt"
    )) {
        $root = $manifest.Directory.FullName

        $lines = @(
            Get-ChildItem `
                -LiteralPath $root `
                -Recurse `
                -File |
            Where-Object {
                $_.FullName -ne $manifest.FullName
            } |
            Sort-Object FullName |
            ForEach-Object {
                $relative = $_.FullName.Substring(
                    $root.Length
                ).TrimStart("\", "/").Replace("\", "/")

                $hash = (
                    Get-FileHash `
                        -LiteralPath $_.FullName `
                        -Algorithm SHA256
                ).Hash.ToLowerInvariant()

                "$hash  $relative"
            }
        )

        [System.IO.File]::WriteAllLines(
            $manifest.FullName,
            $lines,
            $utf8NoBom
        )
    }
}

function Find-ForbiddenArchiveText {
    param([string]$OperationsDirectory)

    $patterns = @(
        "$env:USERPROFILE",
        "$env:USERPROFILE",
        "<LOCAL_USER>"
    )

    $hits = New-Object System.Collections.Generic.List[string]

    foreach ($file in @(
        Get-ChildItem -LiteralPath $OperationsDirectory -Recurse -File
    )) {
        try {
            $text = [System.IO.File]::ReadAllText($file.FullName)
        }
        catch {
            continue
        }

        foreach ($pattern in $patterns) {
            if ($text.Contains($pattern)) {
                $relative = $file.FullName.Substring(
                    $OperationsDirectory.Length
                ).TrimStart("\", "/")

                $hits.Add("$relative :: $pattern")
            }
        }
    }

    return @($hits)
}

function Find-PotentialSecrets {
    param([string]$OperationsDirectory)

    $patterns = @(
        'sk-[A-Za-z0-9]{20,}',
        'ghp_[A-Za-z0-9]{20,}',
        'github_pat_[A-Za-z0-9_]{20,}',
        'AKIA[0-9A-Z]{16}',
        '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----',
        'Authorization:\s*Bearer\s+[A-Za-z0-9._-]+'
    )

    $hits = New-Object System.Collections.Generic.List[string]

    foreach ($file in @(
        Get-ChildItem -LiteralPath $OperationsDirectory -Recurse -File
    )) {
        try {
            $text = [System.IO.File]::ReadAllText($file.FullName)
        }
        catch {
            continue
        }

        foreach ($pattern in $patterns) {
            if ([regex]::IsMatch($text, $pattern)) {
                $relative = $file.FullName.Substring(
                    $OperationsDirectory.Length
                ).TrimStart("\", "/")

                $hits.Add("$relative :: $pattern")
            }
        }
    }

    return @($hits)
}

Write-Host "`n=== WO-006 SANITIZED RECONSTRUCTION PREFLIGHT ==="

if (-not (Test-Path -LiteralPath $repo)) {
    throw "Repository not found: $repo"
}

if (-not (Test-Path -LiteralPath $sourceOperations)) {
    throw "Source operations archive not found: $sourceOperations"
}

if (-not (Test-Path -LiteralPath $originalWorktree)) {
    throw "Original unsanitized WO-006 worktree is missing."
}

$localMainBefore = Get-SingleLine {
    git -C $repo rev-parse refs/heads/main
} "Local main"

$originMainBefore = Get-SingleLine {
    git -C $repo rev-parse refs/remotes/origin/main
} "origin/main"

$liveMainBefore = Get-LiveRemoteMain $repo

foreach ($identity in @(
    $localMainBefore,
    $originMainBefore,
    $liveMainBefore
)) {
    if ($identity -ne $base) {
        throw "Main identity differs from the closed WO-005 base."
    }
}

$originalHead = Get-SingleLine {
    git -C $originalWorktree rev-parse HEAD
} "Original candidate HEAD"

$originalTree = Get-SingleLine {
    git -C $originalWorktree rev-parse "HEAD^{tree}"
} "Original candidate tree"

$originalCurrentBranch = Get-SingleLine {
    git -C $originalWorktree branch --show-current
} "Original candidate branch"

if ($originalHead -ne $originalCandidate) {
    throw "Original unsanitized candidate HEAD changed."
}

if ($originalTree -ne $originalCandidateTree) {
    throw "Original unsanitized candidate tree changed."
}

if ($originalCurrentBranch -ne $originalBranch) {
    throw "Original unsanitized candidate branch changed."
}

if (@(git -C $originalWorktree status --short).Count -ne 0) {
    throw "Original unsanitized candidate worktree is not clean."
}

$sourceStatus = @(
    git -C $repo status --short
)

$sourceUnexpected = @(
    $sourceStatus |
        Where-Object {
            $_ -notmatch '^\?\? tools[/\\]' -and
            $_ -notmatch '^ [MADRCU?!]{1} tools[/\\]' -and
            $_ -notmatch '^[MADRCU?!]{1}  tools[/\\]'
        }
)

if ($sourceUnexpected.Count -gt 0) {
    Write-Host "Unexpected source-worktree paths:"
    $sourceUnexpected | ForEach-Object { Write-Host " - $_" }
    throw "Source worktree contains changes outside tools/**."
}

Assert-OtherWorktreesClean `
    -Repository $repo `
    -AllowedDirty @($repo, $sanitizedWorktree)

$reuseSanitizedWorktree = $false

if (Test-Path -LiteralPath $sanitizedWorktree) {
    $existingBranch = (
        git -C $sanitizedWorktree branch --show-current
    ).Trim()

    $existingHead = (
        git -C $sanitizedWorktree rev-parse HEAD
    ).Trim()

    if ($existingBranch -ne $sanitizedBranch) {
        throw "Existing sanitized worktree has unexpected branch: $existingBranch"
    }

    if ($existingHead -ne $base) {
        throw "Existing sanitized worktree has unexpected HEAD: $existingHead"
    }

    $existingPaths = @(
        git -C $sanitizedWorktree ls-files --others --exclude-standard
        git -C $sanitizedWorktree diff --name-only
        git -C $sanitizedWorktree diff --cached --name-only
    ) | Sort-Object -Unique

    $unexpectedPaths = @(
        $existingPaths |
            Where-Object { $_ -notlike "tools/operations/*" }
    )

    if ($unexpectedPaths.Count -gt 0) {
        Write-Host "Unexpected sanitized-worktree paths:"
        $unexpectedPaths | ForEach-Object { Write-Host " - $_" }
        throw "Existing sanitized worktree contains changes outside tools/operations."
    }

    $reuseSanitizedWorktree = $true
}
elseif (@(git -C $repo branch --list $sanitizedBranch).Count -ne 0) {
    throw "Sanitized branch exists without its expected worktree."
}

$remoteSnapshotBefore = Get-RemoteSnapshot $repo

Write-Host "Base identities, original-candidate preservation, and worktree gates: PASS"

Write-Host "`n=== CREATE SANITIZED WORKTREE ==="

if (-not $reuseSanitizedWorktree) {
    Invoke-Native {
        git -C $repo worktree add `
            -b $sanitizedBranch `
            $sanitizedWorktree `
            $base
    } "Create sanitized worktree" | Out-Null
}
else {
    Write-Host "Reusing preserved sanitized WO-006 worktree."
}

try {
    Write-Host "`n=== COMMIT 1: SANITIZED OPERATIONS ARCHIVE ==="

    $destinationOperations = Join-Path `
        $sanitizedWorktree `
        "tools\operations"

    Copy-DirectoryContents `
        -Source $sourceOperations `
        -Destination $destinationOperations

    if ($PSCommandPath) {
        $scriptDestination = Join-Path `
            $destinationOperations `
            "WO-006\scripts\reconstruct_wo006_sanitized_candidate.ps1"

        New-Item `
            -ItemType Directory `
            -Path (Split-Path -Parent $scriptDestination) `
            -Force | Out-Null

        Copy-Item `
            -LiteralPath $PSCommandPath `
            -Destination $scriptDestination `
            -Force
    }

    $sanitizedFiles = @(
        Sanitize-OperationsArchive $destinationOperations
    )

    $sanitizationManifest = @"
# AEGIS Operations Archive Sanitization Manifest

- Reconstruction date: 2026-08-01
- Public-safe archive base: ``$base``
- Original local archive commit: ``$originalArchive``
- Original local enabling candidate: ``$originalCandidate``
- Original local branch: ``$originalBranch``
- Original local worktree: preserved and unchanged
- Sanitized branch: ``$sanitizedBranch``
- Sanitization scope: ``tools/operations/**``
- Runtime authority granted: no
- Publication authority granted: no

## Purpose

The original archive contains machine-specific absolute paths identifying the
local Windows profile and worktree locations. That original two-commit lineage
remains preserved locally as exact operational evidence but is not eligible for
public publication.

This reconstructed archive is a portable public-safe copy. PowerShell files
replace the original profile prefix with a portable user-profile environment reference. Documentation,
inventories, and other text files replace it with ``<USER_PROFILE>``. Remaining
literal occurrences of the local account label are replaced with
``<LOCAL_USER>``.

Hash inventories are regenerated after sanitization. Consequently, hashes in
this reconstructed archive identify the sanitized copies, not the preserved
private originals.

## Preservation boundary

This sanitization does not alter the original branch, original commits, main,
origin/main, live remote main, tags, rulesets, runtime, tests, benchmarks,
dependencies, CI, releases, or existing worktrees.
"@

    Write-Utf8NoBom `
        -Path (Join-Path $destinationOperations "SANITIZATION_MANIFEST.md") `
        -Content ($sanitizationManifest.TrimEnd() + "`n")

    Update-ScriptInventory $destinationOperations
    Regenerate-HashManifests $destinationOperations

    $forbiddenText = @(
        Find-ForbiddenArchiveText $destinationOperations
    )

    if ($forbiddenText.Count -gt 0) {
        Write-Host "Forbidden local-path remnants:"
        $forbiddenText | ForEach-Object { Write-Host " - $_" }
        throw "Sanitized archive still contains local identity/path text."
    }

    $secretHits = @(
        Find-PotentialSecrets $destinationOperations
    )

    if ($secretHits.Count -gt 0) {
        Write-Host "Potential secret findings:"
        $secretHits | ForEach-Object { Write-Host " - $_" }
        throw "Potential credentials detected in sanitized archive."
    }

    $archivePathsBeforeStage = @(
        git -C $sanitizedWorktree ls-files --others --exclude-standard
        git -C $sanitizedWorktree diff --name-only
    ) | Sort-Object -Unique

    if ($archivePathsBeforeStage.Count -eq 0) {
        throw "No sanitized archive files were prepared."
    }

    $archiveEscapes = @(
        $archivePathsBeforeStage |
            Where-Object { $_ -notlike "tools/operations/*" }
    )

    if ($archiveEscapes.Count -gt 0) {
        throw "Sanitized archive preparation escaped tools/operations/**."
    }

    Invoke-Native {
        git -C $sanitizedWorktree add -- tools/operations
    } "Stage sanitized archive" | Out-Null

    $stagedArchivePaths = @(
        git -C $sanitizedWorktree diff --cached --name-only
    )

    $stagedArchiveEscapes = @(
        $stagedArchivePaths |
            Where-Object { $_ -notlike "tools/operations/*" }
    )

    if ($stagedArchivePaths.Count -eq 0) {
        throw "No sanitized archive paths were staged."
    }

    if ($stagedArchiveEscapes.Count -gt 0) {
        throw "Staged sanitized archive escaped tools/operations/**."
    }

    $archiveWhitespace = Invoke-Native {
        git -C $sanitizedWorktree diff --cached --check
    } "Sanitized archive whitespace scan" -AllowFailure

    if ($archiveWhitespace.ExitCode -ne 0) {
        Write-Host "Historical whitespace findings remain non-blocking archive evidence:"
        $archiveWhitespace.Output |
            Select-Object -First 30 |
            ForEach-Object { Write-Host " - $_" }
    }

    Invoke-Native {
        git -C $sanitizedWorktree commit -m $archiveSubject
    } "Create sanitized archive commit" | Out-Null

    $sanitizedArchiveCommit = Get-SingleLine {
        git -C $sanitizedWorktree rev-parse HEAD
    } "Sanitized archive commit"

    $sanitizedArchiveParent = Get-SingleLine {
        git -C $sanitizedWorktree rev-parse HEAD^
    } "Sanitized archive parent"

    $sanitizedArchiveTree = Get-SingleLine {
        git -C $sanitizedWorktree rev-parse "HEAD^{tree}"
    } "Sanitized archive tree"

    if ($sanitizedArchiveParent -ne $base) {
        throw "Sanitized archive parent mismatch."
    }

    $committedArchivePaths = @(
        git -C $sanitizedWorktree diff-tree `
            --no-commit-id `
            --name-only `
            -r `
            $sanitizedArchiveCommit
    )

    if (
        @(
            $committedArchivePaths |
                Where-Object { $_ -notlike "tools/operations/*" }
        ).Count -gt 0
    ) {
        throw "Sanitized archive commit escaped tools/operations/**."
    }

    foreach ($needle in @(
        "$env:USERPROFILE",
        "$env:USERPROFILE",
        "<LOCAL_USER>"
    )) {
        $scan = Invoke-Native {
            git -C $sanitizedWorktree grep `
                -n `
                -I `
                -F `
                $needle `
                $sanitizedArchiveCommit `
                -- `
                tools/operations
        } "Committed archive scan for $needle" -AllowFailure

        if ($scan.ExitCode -eq 0 -and $scan.Output.Count -gt 0) {
            throw "Committed sanitized archive still contains '$needle'."
        }
    }

    Write-Host "Sanitized archive commit: $sanitizedArchiveCommit"

    Write-Host "`n=== COMMIT 2: SANITIZED WO-006 ENABLING BOUNDARY ==="

    $specText = Read-CommitFile `
        -Repository $repo `
        -Commit $originalCandidate `
        -Path $specRelative

    $traceText = Read-CommitFile `
        -Repository $repo `
        -Commit $originalCandidate `
        -Path $traceRelative

    $workOrderText = Read-CommitFile `
        -Repository $repo `
        -Commit $originalCandidate `
        -Path $workOrderRelative

    $traceText = $traceText.Replace(
        $originalArchive,
        $sanitizedArchiveCommit
    )

    $workOrderText = $workOrderText.Replace(
        $originalArchive,
        $sanitizedArchiveCommit
    )

    $sanitizedTraceSection = @"

### Sanitized reconstruction

- Original local archive commit: ``$originalArchive``
- Original local enabling candidate: ``$originalCandidate``
- Original local candidate disposition: preserved as private operational evidence; not eligible for publication
- Sanitized operations-archive commit: ``$sanitizedArchiveCommit``
- Sanitized archive tree: ``$sanitizedArchiveTree``
- Personal absolute paths removed: yes
- Common credential-pattern scan: pass
- Hash inventories regenerated: yes
- Runtime, tests, benchmarks, dependencies, and CI changes: none
- Main and remote references changed: no
- Publication authority granted by reconstruction: no

This reconstruction supersedes the original local candidate only as the
publication-eligible WO-006 enabling candidate. It does not invalidate or
delete the preserved private evidence lineage and does not authorize runtime
implementation, benchmark implementation, integration, publication, tags,
releases, ruleset changes, or worktree cleanup.
"@

    if (-not $traceText.Contains("### Sanitized reconstruction")) {
        $traceText = $traceText.TrimEnd() + $sanitizedTraceSection + "`n"
    }

    $sanitizedWorkOrderSection = @"

## Sanitized public-candidate reconstruction

- Original private archive commit: ``$originalArchive``
- Original private enabling candidate: ``$originalCandidate``
- Sanitized archive commit: ``$sanitizedArchiveCommit``
- Sanitized archive tree: ``$sanitizedArchiveTree``
- Original lineage preservation: required; no cleanup authorized
- Runtime implementation authority: not granted
- Benchmark implementation authority: not granted
- Integration and publication authority: not granted

The original local candidate remains exact operational evidence but contains
machine-specific absolute paths. This reconstructed candidate replaces those
paths in the public-safe archive, regenerates archive hashes, and retains the
same accepted specification correction and WO-006 enabling boundary.

The sanitization changes no architecture, runtime contract, package allowlist,
test allowlist, benchmark obligation, security boundary, or activation gate.
"@

    if (-not $workOrderText.Contains("## Sanitized public-candidate reconstruction")) {
        $workOrderText = (
            $workOrderText.TrimEnd() +
            $sanitizedWorkOrderSection +
            "`n"
        )
    }

    Write-Utf8NoBom `
        -Path (Join-Path $sanitizedWorktree $specRelative) `
        -Content ($specText.TrimEnd() + "`n")

    Write-Utf8NoBom `
        -Path (Join-Path $sanitizedWorktree $traceRelative) `
        -Content ($traceText.TrimEnd() + "`n")

    Write-Utf8NoBom `
        -Path (Join-Path $sanitizedWorktree $workOrderRelative) `
        -Content ($workOrderText.TrimEnd() + "`n")

    $governanceChangedPaths = @(
        git -C $sanitizedWorktree status --short |
            ForEach-Object { $_.Substring(3) }
    )

    Assert-ExactPathSet `
        -Actual $governanceChangedPaths `
        -Expected $governancePaths `
        -Label "Sanitized enabling governance boundary"

    Invoke-Native {
        git -C $sanitizedWorktree diff --check
    } "Validate sanitized enabling governance changes" | Out-Null

    $forbiddenTechnicalChanges = @(
        git -C $sanitizedWorktree diff `
            --name-only `
            $sanitizedArchiveCommit `
            -- `
            aegis_os `
            tests `
            benchmarks `
            pyproject.toml `
            .github
    )

    if ($forbiddenTechnicalChanges.Count -gt 0) {
        throw "Sanitized enabling candidate contains forbidden technical changes."
    }

    Invoke-Native {
        git -C $sanitizedWorktree add -- $governancePaths
    } "Stage sanitized enabling governance changes" | Out-Null

    $stagedGovernancePaths = @(
        git -C $sanitizedWorktree diff --cached --name-only
    )

    Assert-ExactPathSet `
        -Actual $stagedGovernancePaths `
        -Expected $governancePaths `
        -Label "Staged sanitized enabling governance boundary"

    Invoke-Native {
        git -C $sanitizedWorktree diff --cached --check
    } "Validate staged sanitized enabling governance changes" | Out-Null

    Invoke-Native {
        git -C $sanitizedWorktree commit -m $enablingSubject
    } "Create sanitized enabling commit" | Out-Null

    $sanitizedCandidate = Get-SingleLine {
        git -C $sanitizedWorktree rev-parse HEAD
    } "Sanitized enabling candidate"

    $sanitizedCandidateParent = Get-SingleLine {
        git -C $sanitizedWorktree rev-parse HEAD^
    } "Sanitized enabling parent"

    $sanitizedCandidateTree = Get-SingleLine {
        git -C $sanitizedWorktree rev-parse "HEAD^{tree}"
    } "Sanitized enabling tree"

    if ($sanitizedCandidateParent -ne $sanitizedArchiveCommit) {
        throw "Sanitized enabling parent mismatch."
    }

    $committedGovernancePaths = @(
        git -C $sanitizedWorktree diff-tree `
            --no-commit-id `
            --name-only `
            -r `
            $sanitizedCandidate
    )

    Assert-ExactPathSet `
        -Actual $committedGovernancePaths `
        -Expected $governancePaths `
        -Label "Committed sanitized enabling governance boundary"

    Write-Host "Sanitized enabling candidate: $sanitizedCandidate"

    Write-Host "`n=== VERIFY SANITIZED LINEAGE AND PRESERVATION ==="

    $commitCount = [int](Get-SingleLine {
        git -C $sanitizedWorktree rev-list `
            --count `
            "$base..$sanitizedCandidate"
    } "Sanitized lineage commit count")

    $mergeCount = @(
        git -C $sanitizedWorktree rev-list `
            --merges `
            "$base..$sanitizedCandidate"
    ).Count

    if ($commitCount -ne 2) {
        throw "Expected exactly two commits in sanitized lineage."
    }

    if ($mergeCount -ne 0) {
        throw "Sanitized lineage contains a merge commit."
    }

    if (@(git -C $sanitizedWorktree status --short).Count -ne 0) {
        throw "Sanitized enabling worktree is not clean."
    }

    $originalHeadAfter = Get-SingleLine {
        git -C $originalWorktree rev-parse HEAD
    } "Original candidate preservation"

    if ($originalHeadAfter -ne $originalCandidate) {
        throw "Original unsanitized candidate changed during reconstruction."
    }

    $localMainAfter = Get-SingleLine {
        git -C $repo rev-parse refs/heads/main
    } "Local main after reconstruction"

    $originMainAfter = Get-SingleLine {
        git -C $repo rev-parse refs/remotes/origin/main
    } "origin/main after reconstruction"

    $liveMainAfter = Get-LiveRemoteMain $repo

    foreach ($identity in @(
        $localMainAfter,
        $originMainAfter,
        $liveMainAfter
    )) {
        if ($identity -ne $base) {
            throw "Main changed during sanitized reconstruction."
        }
    }

    $remoteSnapshotAfter = Get-RemoteSnapshot $repo

    Assert-SequenceEqual `
        -Before $remoteSnapshotBefore `
        -After $remoteSnapshotAfter `
        -Label "Remote heads and tags"

    $technicalChanges = @(
        git -C $sanitizedWorktree diff `
            --name-only `
            $base `
            $sanitizedCandidate `
            -- `
            aegis_os `
            tests `
            benchmarks `
            pyproject.toml `
            .github
    )

    if ($technicalChanges.Count -gt 0) {
        throw "Sanitized lineage contains technical changes."
    }

    New-Item `
        -ItemType Directory `
        -Path $logDirectory `
        -Force | Out-Null

    $manifest = @"
AEGIS WO-006 Sanitized Enabling Reconstruction
==============================================

Date: 2026-08-01

Authoritative base:
$base

Preserved original private archive:
$originalArchive

Preserved original private enabling candidate:
$originalCandidate

Sanitized archive commit:
$sanitizedArchiveCommit

Sanitized archive parent:
$sanitizedArchiveParent

Sanitized archive tree:
$sanitizedArchiveTree

Sanitized archive subject:
$archiveSubject

Sanitized archive path count:
$($committedArchivePaths.Count)

Sanitized enabling candidate:
$sanitizedCandidate

Sanitized enabling parent:
$sanitizedCandidateParent

Sanitized enabling tree:
$sanitizedCandidateTree

Sanitized enabling subject:
$enablingSubject

Sanitized governance paths:
$($committedGovernancePaths -join "`r`n")

Validation:
- Local lineage commit count: 2
- Merge commit count: 0
- Local personal path references: 0
- Common credential-pattern findings: 0
- Runtime changes: 0
- Test changes: 0
- Benchmark changes: 0
- Dependency changes: 0
- CI changes: 0
- Local main changed: NO
- origin/main changed: NO
- Live remote main changed: NO
- Remote heads or tags changed: NO
- Original private branch changed: NO
- Push performed: NO
- Tag created: NO
- Release created: NO
- Ruleset changed: NO
- Worktree cleanup performed: NO
- Runtime implementation authority: NO
- Publication authority: NO
- Final state: WO-006 SANITIZED LOCAL ENABLING CANDIDATE - REVIEW REQUIRED
"@

    [System.IO.File]::WriteAllText(
        $manifestPath,
        $manifest,
        $utf8NoBom
    )

    Write-Host "`n=== WO-006 SANITIZED RECONSTRUCTION RESULT ==="

    [pscustomobject]@{
        AuthoritativeBase = $base
        OriginalPrivateArchive = $originalArchive
        OriginalPrivateCandidate = $originalCandidate
        OriginalPrivateCandidatePreserved = $true
        SanitizedArchiveCommit = $sanitizedArchiveCommit
        SanitizedArchiveParent = $sanitizedArchiveParent
        SanitizedArchiveTree = $sanitizedArchiveTree
        SanitizedArchiveSubject = $archiveSubject
        SanitizedArchivePathCount = $committedArchivePaths.Count
        SanitizedCandidate = $sanitizedCandidate
        SanitizedCandidateParent = $sanitizedCandidateParent
        SanitizedCandidateTree = $sanitizedCandidateTree
        SanitizedCandidateSubject = $enablingSubject
        SanitizedGovernancePathCount = $committedGovernancePaths.Count
        LocalCommitCount = $commitCount
        MergeCommitCount = $mergeCount
        PersonalPathReferences = 0
        CredentialPatternFindings = 0
        RuntimeChanges = 0
        TestChanges = 0
        BenchmarkChanges = 0
        DependencyChanges = 0
        CIChanges = 0
        LocalMain = $localMainAfter
        OriginMain = $originMainAfter
        LiveRemoteMain = $liveMainAfter
        PushPerformed = $false
        TagCreated = $false
        ReleaseCreated = $false
        RulesetChanged = $false
        WorktreeCleanupPerformed = $false
        RuntimeImplementationAuthorized = $false
        PublicationAuthorized = $false
        SanitizedWorktreeClean = $true
        Branch = $sanitizedBranch
        Worktree = $sanitizedWorktree
        Manifest = $manifestPath
        FinalStatus = "WO-006 SANITIZED LOCAL ENABLING CANDIDATE - REVIEW REQUIRED"
    } | Format-List

    Write-Host "Sanitized governance paths:"
    $committedGovernancePaths |
        ForEach-Object { Write-Host " - $_" }

    Write-Host "`nWO-006 SANITIZED RECONSTRUCTION: COMPLETE"
    Write-Host "No push, runtime implementation, main modification, tag, release, ruleset change, or worktree cleanup was performed."
}
catch {
    if (Test-Path -LiteralPath $sanitizedWorktree) {
        Write-Host "`nSanitized worktree preserved for diagnosis:"
        git -C $sanitizedWorktree status --short
    }

    throw
}
