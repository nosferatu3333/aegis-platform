# AEGIS Operations Archive Sanitization Manifest

- Reconstruction date: 2026-08-01
- Public-safe archive base: `cfae92111eeb5355873a8c32c649514853564743`
- Original local archive commit: `12486b34f46f82bd9103fa339a5cc0e849261bf6`
- Original local enabling candidate: `0bdd8ce58566c806136f1d85347d593fb7c27cbd`
- Original local branch: `governance/wo-006-enabling`
- Original local worktree: preserved and unchanged
- Sanitized branch: `governance/wo-006-enabling-sanitized`
- Sanitization scope: `tools/operations/**`
- Runtime authority granted: no
- Publication authority granted: no

## Purpose

The original archive contains machine-specific absolute paths identifying the
local Windows profile and worktree locations. That original two-commit lineage
remains preserved locally as exact operational evidence but is not eligible for
public publication.

This reconstructed archive is a portable public-safe copy. PowerShell files
replace the original profile prefix with a portable user-profile environment reference. Documentation,
inventories, and other text files replace it with `<USER_PROFILE>`. Remaining
literal occurrences of the local account label are replaced with
`<LOCAL_USER>`.

Hash inventories are regenerated after sanitization. Consequently, hashes in
this reconstructed archive identify the sanitized copies, not the preserved
private originals.

## Preservation boundary

This sanitization does not alter the original branch, original commits, main,
origin/main, live remote main, tags, rulesets, runtime, tests, benchmarks,
dependencies, CI, releases, or existing worktrees.
