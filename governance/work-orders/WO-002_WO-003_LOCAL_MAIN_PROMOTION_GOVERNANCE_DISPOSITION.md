# WO-002/WO-003 Local-Main Promotion Governance Disposition

**Governance disposition:** ACCEPTED — ELIGIBLE FOR CONTROLLED REMOTE PUBLICATION
**Date recorded:** 2026-07-30
**Promotion authorization:** `e69c724d430b307ecaaffdb0c3b8646ef5511280`
**Old local `main`:** `c137005b08c449a8e19f7734098865dd10181955`
**Promoted local `main`:** `f727d9f9f2b82b55f79e31008bb79b71477fbc84`
**Promoted tree:** `23f458c2d8a1576c8068aac3de0350dbc792d421`
**Release promotion verdict:** PASS
**Rollback performed:** NO
**Remote publication authority:** NOT GRANTED
**Next eligible owner:** Release & Integration Engineer — separate explicit controlled remote-publication authorization required

---

## Purpose

This record reconciles the completed atomic local-`main` promotion with the authorized identity, ancestry, validation, preservation, and non-authority controls. It determines whether the promoted local state is eligible for a separately controlled remote publication.

This disposition accepts the local promotion. It does not authorize push, remote modification, publication, release, cleanup, or WO-004 activation.

## Promotion Identity

| Control | Exact identity |
|---|---|
| Promotion authorization | `e69c724d430b307ecaaffdb0c3b8646ef5511280` |
| Expected old local `main` | `c137005b08c449a8e19f7734098865dd10181955` |
| Promoted local `main` | `f727d9f9f2b82b55f79e31008bb79b71477fbc84` |
| Promoted tree | `23f458c2d8a1576c8068aac3de0350dbc792d421` |
| Promotion method | Atomic compare-and-swap `git update-ref` fast-forward |
| Atomic result | **PASS** |
| Rollback | **NOT REQUIRED; NOT PERFORMED** |

The promoted local reference points to the exact integration object previously accepted by Release & Integration, QA & Verification, Architecture, and Governance.

## Preserved Two-Commit Ancestry

The local `main` history remains:

```text
c137005b08c449a8e19f7734098865dd10181955
└─ fb0364d1b4e0a27953ea7d683a786193d6e61c48
   Integrate authorized WO-002 foundation
   └─ f727d9f9f2b82b55f79e31008bb79b71477fbc84
      Integrate exact WO-003 Candidate 2 overlay
```

Integration A remains the direct, sole child of the protected base. Integration B remains the direct, sole child of Integration A. There are exactly two commits after the old local `main`, with no merge, intermediate, alternate-lineage, or governance commit.

## Preliminary Read-Only Preflight Reconciliation

Release & Integration performed a preliminary read-only preflight that stopped before promotion. The stop produced no reference, index, worktree, object, remote, or content mutation. The preflight condition was corrected, the mandatory gates were re-evaluated, and the authorized atomic compare-and-swap subsequently passed.

Because the stop was non-mutating, resolved before promotion, and followed by complete successful verification, it is recorded as a correctly handled preflight event and not as a promotion defect.

## Boundary and Blob Preservation

The promoted base-to-tip delta remains exactly 21 authorized paths:

- Stage 1 contains exactly nine WO-002 paths whose blobs match authoritative source `4d1842087289336675d43d7cd650bd80f57b8c8d`.
- Stage 2 contains exactly sixteen WO-003 paths whose final blobs match Candidate 2 commit `eee135547a768c3cad95c1e2e5342e9203620463`.
- The stages overlap on exactly four paths.
- Unauthorized paths: `0`.
- Governance paths: `0`.
- Infrastructure and workspace paths: `0`.
- Integration-specific semantic adaptation: none.

Integration A, Integration B, and the promoted tree remain unchanged.

## Post-Promotion Evidence Reconciliation

| Gate | Result |
|---|---|
| Release promotion verdict | **PASS** |
| CPython | `3.11.9` |
| Focused runtime/API/analyze validation | `52 passed` |
| Complete WO-003 validation | `97 passed` |
| Complete repository suite | `172 passed` |
| Dependency integrity | **PASS** |
| Scoped Ruff lint | **PASS — exact 18 Python paths** |
| Ruff format-check | **PASS** |
| Repository-wide Ruff no-regression | **PASS** |
| Exact 21-path boundary | **PASS** |
| Unauthorized paths | `0` |
| `git diff --check` | **PASS** |
| Clean promoted-tree validation | **PASS** |

The post-promotion evidence reproduces the accepted integration evidence against the exact promoted object.

## Ruff No-Regression Status

The exact eighteen Python paths pass direct Ruff lint and format-check. Repository-wide Ruff output remains exactly equal to the accepted protected-base three-diagnostic baseline:

1. `aegis_os/knowledge/knowledge_graph.py:1:40` — `F401`.
2. `aegis_os/knowledge/knowledge_graph.py:2:45` — `F401`.
3. `aegis_os/pipeline/__init__.py:26:54` — `F401`.

No authorized path has a Ruff diagnostic. The inherited baseline remains unchanged and unremediated.

## Recovery and Reference Preservation

| Protected object | Preserved identity |
|---|---|
| Recovery tag object | `9406fc75ecd6ddc5ef45adeff4042587dfdb2bf8` |
| Recovery target | `c137005b08c449a8e19f7734098865dd10181955` |
| Candidate 1 tag object | `cfbefaa046b043d2fa0b099a967f2936915499f8` |
| Candidate 1 commit | `7651fe4ac2fe242459d9864fb9256920fe3b2d9f` |
| Candidate 2 tag object | `3b674e57b18568fe1e2a4509f8448ffeaff647ee` |
| Candidate 2 commit | `eee135547a768c3cad95c1e2e5342e9203620463` |
| Integration A | `fb0364d1b4e0a27953ea7d683a786193d6e61c48` |
| Integration B | `f727d9f9f2b82b55f79e31008bb79b71477fbc84` |

Rollback was not required and was not performed. The recovery authority remains unused.

## Unrelated-Work Preservation

The two unrelated documentation modifications remained outside the promotion environment and retain their recorded SHA-256 hashes:

| Path | Preserved SHA-256 |
|---|---|
| `docs/AEGIS_CURRENT_STATE_DIAGNOSTIC.md` | `085BF9CB521B5DF6E98FADCE99A8E495A6A80EE3C89853C55BFFBCDA2CBF79AA` |
| `docs/audits/IMPLEMENTATION_GAP_ANALYSIS.md` | `DA2FA2FDAF0F6BE0718DF5505B7D5825B85DEBC54857CB79C62C564CA7C21806` |

They were not staged, restored, formatted, stashed, cleaned, committed, or copied into local `main`.

## Remote State

Local and remote state are intentionally different after the local-only promotion:

| Reference | Current identity |
|---|---|
| Local `main` | `f727d9f9f2b82b55f79e31008bb79b71477fbc84` |
| Remote-tracking `origin/main` | `c137005b08c449a8e19f7734098865dd10181955` |
| Live remote `main` | `c137005b08c449a8e19f7734098865dd10181955` |

No push or remote mutation occurred.

## Deferred Technical Debt

No promotion defect or new debt was introduced. The previously accepted non-blocking debt remains:

1. Three inherited protected-base Ruff `F401` diagnostics.
2. Duplicate canonical-status derivation.
3. Limited dashboard rendering of structured non-2xx conformance evidence.
4. Possible future expansion of the internal-fault taxonomy.

Each item remains outside this promotion and requires separate authorization if pursued.

## Governance Determination

The atomic local promotion, exact promoted identity, two-commit ancestry, post-promotion validation, path and blob boundary, Ruff no-regression state, protected references, unrelated work, and remote non-mutation all satisfy the controlled promotion authorization.

There is no additional local-evidence requirement and no promotion defect.

The final disposition is:

```text
ACCEPTED — ELIGIBLE FOR CONTROLLED REMOTE PUBLICATION
```

This disposition establishes eligibility only.

## Remote-Publication Boundary

Release & Integration is the next eligible owner but may not push or modify any remote reference until a separate explicit controlled remote-publication authorization defines:

- Exact local source and remote target identities.
- Remote compare-and-swap or lease protection.
- Permitted reference and push command.
- Pre-publication remote-divergence checks.
- Post-publication identity and validation requirements.
- Recovery and failure procedures.
- Publication evidence and final governance handoff.

Until that authority exists, the following remain prohibited:

- Push or any remote reference modification.
- Force push or weakened lease protection.
- Tag publication or mutation.
- Modification of local `main`, Integration A, or Integration B.
- Merge, rebase, squash, cherry-pick, amendment, or reconstruction.
- Governance-history projection.
- Cleanup or deletion of branches, worktrees, tags, or recovery objects.
- Unrelated documentation changes.
- Release publication or deployment.
- WO-004 activation.

```text
Promotion authorization: e69c724d430b307ecaaffdb0c3b8646ef5511280
Old local main: c137005b08c449a8e19f7734098865dd10181955
Promoted local main: f727d9f9f2b82b55f79e31008bb79b71477fbc84
Promoted tree: 23f458c2d8a1576c8068aac3de0350dbc792d421
Release verdict: PASS
Post-promotion validation: PASS — CPYTHON 3.11.9; 52 FOCUSED; 97 WO-003; 172 FULL
Governance disposition: ACCEPTED — ELIGIBLE FOR CONTROLLED REMOTE PUBLICATION
Governance disposition commit: RECORDED BY THE COMMIT CONTAINING THIS DOCUMENT
Local promotion accepted: YES
Remote main: c137005b08c449a8e19f7734098865dd10181955
Remote publication authorized: NO
Push authorized: NO
Rollback required: NO
WO-004 authorized: NO
Next eligible owner: RELEASE & INTEGRATION ENGINEER
Required next authorization: SEPARATE EXPLICIT CONTROLLED REMOTE-PUBLICATION AUTHORIZATION
```
