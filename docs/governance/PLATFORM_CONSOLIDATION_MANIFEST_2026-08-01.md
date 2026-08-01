# Platform Consolidation Manifest — 2026-08-01

The uploaded delivery contained one Git repository named `aegis-platform` and
multiple non-Git work-order snapshots. This repository is the sole canonical
implementation lineage used for WO-MVP-006.

The final delivery intentionally contains only this repository. External
folders named for WO-003 through WO-006, candidate review, amendment,
publication, closure, governance, and sanitized exports are treated as source
snapshots or evidence packages rather than independent Platform repositories.
No competing code tree is copied into the canonical repository.

Canonical baseline before WO-MVP-006:

- branch: `phase-1/canonical-execution-pipeline-clean`
- commit: `3bf2c3a`
- baseline tests: 172 passed
- untracked operational inventory under `tools/` classified as staging material and excluded from the canonical repository; it remains preserved in the original uploaded source archive

Canonical implementation branch:

- `feat/wo-mvp-006-bounded-planning-adapter`
