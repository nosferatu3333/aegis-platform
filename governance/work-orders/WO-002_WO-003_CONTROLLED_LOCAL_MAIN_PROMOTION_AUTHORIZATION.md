# WO-002/WO-003 Controlled Local-Main Promotion Authorization

**Authorization status:** AUTHORIZED — CONTROLLED LOCAL-MAIN FAST-FORWARD PROMOTION ONLY
**Date authorized:** 2026-07-30
**Old local `main`:** `c137005b08c449a8e19f7734098865dd10181955`
**Authorized promotion target:** `f727d9f9f2b82b55f79e31008bb79b71477fbc84`
**Authorized target tree:** `23f458c2d8a1576c8068aac3de0350dbc792d421`
**Governance disposition:** `281755539a492874a28d9e74b2fddb35706752b3`
**Active owner:** Release & Integration Engineer
**Remote modification:** NOT AUTHORIZED
**Push:** NOT AUTHORIZED
**WO-004:** NOT AUTHORIZED

---

## Purpose

This authorization permits Release & Integration to promote the exact accepted WO-002/WO-003 bounded integration commit to local `main` through one atomic compare-and-swap reference update.

The authority is conditional on every pre-promotion identity and preservation gate. It grants no authority to modify content, create another commit, merge, push, publish, release, or activate WO-004.

## Accepted Promotion Objects

| Control | Exact identity |
|---|---|
| Protected base / expected old `main` | `c137005b08c449a8e19f7734098865dd10181955` |
| Integration A | `fb0364d1b4e0a27953ea7d683a786193d6e61c48` |
| Integration B / accepted target | `f727d9f9f2b82b55f79e31008bb79b71477fbc84` |
| Accepted target tree | `23f458c2d8a1576c8068aac3de0350dbc792d421` |
| Recovery tag | `recovery/pre-wo-002-wo-003-integration-c137005b` |
| Recovery tag object | `9406fc75ecd6ddc5ef45adeff4042587dfdb2bf8` |
| Recovery target | `c137005b08c449a8e19f7734098865dd10181955` |

The only accepted history is:

```text
c137005b08c449a8e19f7734098865dd10181955
└─ fb0364d1b4e0a27953ea7d683a786193d6e61c48
   └─ f727d9f9f2b82b55f79e31008bb79b71477fbc84
```

## Mandatory Pre-Promotion Gates

Immediately before promotion, Release & Integration must independently verify:

1. `refs/heads/main` equals exact protected base `c137005b08c449a8e19f7734098865dd10181955`.
2. `refs/remotes/origin/main` equals exact protected base `c137005b08c449a8e19f7734098865dd10181955`.
3. Live `refs/heads/main` at the configured `origin`, when reachable, equals exact protected base `c137005b08c449a8e19f7734098865dd10181955`.
4. `refs/heads/integration/wo-002-wo-003-c137005b` equals exact target `f727d9f9f2b82b55f79e31008bb79b71477fbc84`.
5. The target tree equals `23f458c2d8a1576c8068aac3de0350dbc792d421`.
6. Integration A is the direct, sole child of the protected base.
7. Integration B is the direct, sole child of Integration A.
8. The protected-base-to-target range contains exactly two commits.
9. The final protected-base-to-target delta contains exactly the accepted 21 paths and zero unauthorized paths.
10. Recovery tag object `9406fc75ecd6ddc5ef45adeff4042587dfdb2bf8` still peels to the protected base.
11. Candidate 1 remains at tag object `cfbefaa046b043d2fa0b099a967f2936915499f8` and commit `7651fe4ac2fe242459d9864fb9256920fe3b2d9f`.
12. Candidate 2 remains at tag object `3b674e57b18568fe1e2a4509f8448ffeaff647ee` and commit `eee135547a768c3cad95c1e2e5342e9203620463`.
13. No worktree currently checks out `main`.
14. The isolated integration worktree is clean at exact target SHA.
15. The unrelated documentation remains outside the promotion environment with unchanged hashes.
16. The configured remote URL and repository identity have not changed.
17. No local, remote-tracking, or reachable live remote identity has diverged from the expected state.

The preserved unrelated-document hashes are:

| Path | Required SHA-256 |
|---|---|
| `docs/AEGIS_CURRENT_STATE_DIAGNOSTIC.md` | `085BF9CB521B5DF6E98FADCE99A8E495A6A80EE3C89853C55BFFBCDA2CBF79AA` |
| `docs/audits/IMPLEMENTATION_GAP_ANALYSIS.md` | `DA2FA2FDAF0F6BE0718DF5505B7D5825B85DEBC54857CB79C62C564CA7C21806` |

If live remote `main` is unreachable, Release & Integration must record that limitation and must still verify the remote-tracking reference. Unreachability grants no remote authority. Any observed identity mismatch is a stop condition.

## Worktree Condition

This authorization permits the atomic reference-update method only while no worktree checks out `main`.

If `main` becomes checked out in any worktree before execution, stop. This record does not authorize silent `update-ref`, creation of another promotion worktree, checkout manipulation, or an alternate promotion mechanism.

## Authorized Promotion Method

After all pre-promotion gates pass, the only authorized promotion command is:

```powershell
git update-ref refs/heads/main `
  f727d9f9f2b82b55f79e31008bb79b71477fbc84 `
  c137005b08c449a8e19f7734098865dd10181955
```

The expected old SHA is mandatory. The command is an atomic compare-and-swap update:

- It may succeed only if local `main` still equals the protected base.
- It must fail rather than overwrite any divergent local `main`.
- The resulting update must be a true fast-forward along the exact accepted two-commit ancestry.

No force flag or alternate reference-update command is authorized.

## Prohibited Promotion Methods

The following are prohibited:

- Merge commit.
- Squash merge.
- Cherry-pick.
- Rebase.
- Fast-forward through a mutable or different target.
- Content reconstruction.
- Conflict resolution.
- Blob modification.
- Commit amendment.
- Additional integration or promotion commit.
- Checkout-based promotion in the shared dirty governance worktree.
- Any update lacking the exact old-value compare-and-swap guard.

## Immediate Post-Update Identity Verification

If the atomic update succeeds, verify before running broader validation:

1. Local `main` equals `f727d9f9f2b82b55f79e31008bb79b71477fbc84`.
2. Local `main^{tree}` equals `23f458c2d8a1576c8068aac3de0350dbc792d421`.
3. Local `main` has Integration A as its parent.
4. Integration A has protected base as its parent.
5. The protected-base-to-`main` range contains exactly two commits.
6. The base-to-`main` delta remains the exact accepted 21 paths.
7. Integration A and Integration B identities remain unchanged.
8. Recovery and candidate references remain unchanged.
9. Remote-tracking `origin/main` remains at the protected base.
10. Reachable live remote `main` remains at the protected base.
11. No remote reference was modified.
12. Unrelated documentation hashes remain unchanged.

Any failed identity check triggers the recovery procedure.

## Post-Promotion Validation Gates

Validation must run against exact promoted commit `f727d9f9f2b82b55f79e31008bb79b71477fbc84` in the existing clean integration worktree or an evidence-only clean export of the exact local-`main` object. Do not check out `main` in the shared governance worktree.

Using CPython 3.11, Release & Integration must obtain:

- Focused runtime/API/analyze validation: pass.
- Complete WO-003 validation: pass.
- Complete repository suite: pass.
- Dependency integrity: pass.
- Exact 18-path Python Ruff lint: pass.
- Exact 18-path Python Ruff format-check: pass.
- Repository-wide Ruff normalized output: exact equality with the accepted three-diagnostic protected-base baseline.
- Candidate 2 blob equality for the three non-Python boundary paths: pass.
- `git diff --check`: pass.
- Exact 21-path boundary: pass.
- Clean validation environment before and after validation.
- Reproducible promoted tree identity: pass.

The report must record the exact Python and Ruff versions, commands, counts, outcomes, and environment.

## Stop Conditions

Stop without promotion if:

- Any pre-promotion identity, ancestry, boundary, reference, worktree, remote, or preservation gate fails.
- Local `main` is checked out in a worktree.
- The accepted target or tree changes.
- The integration worktree is not clean.
- An unrelated documentation hash changes.
- The atomic compare-and-swap command cannot be used exactly as authorized.
- Any semantic, content, conflict-resolution, or alternate-history action would be required.

If the atomic update fails, treat local `main` as unchanged until independently verified. Do not retry with a force operation or weakened old-value guard.

If a post-update identity or validation gate fails, invoke only the authorized recovery procedure and report the failure.

## Authorized Recovery Procedure

If local promotion succeeded but a post-update gate fails, Release & Integration is authorized to attempt exactly one atomic local rollback:

```powershell
git update-ref refs/heads/main `
  c137005b08c449a8e19f7734098865dd10181955 `
  f727d9f9f2b82b55f79e31008bb79b71477fbc84
```

This rollback is authorized only when local `main` still equals the accepted target. The exact expected current value is mandatory.

After a successful rollback, verify:

- Local `main` equals the protected base.
- Remote-tracking and live remote `main` remain unchanged.
- Integration A, Integration B, recovery, and candidate references remain unchanged.
- Unrelated documentation remains untouched.

Preserve all integration commits, branches, worktrees, tags, governance records, and failure evidence. Cleanup, deletion, reset, force update, rebase, and retry are not authorized.

If the rollback compare-and-swap fails, stop and escalate. Do not force or overwrite the observed state.

## Explicit Restrictions

This authorization does not permit:

- Push or any remote modification.
- Merge commits or any non-fast-forward history.
- Force update.
- Tag creation, movement, replacement, or deletion.
- Candidate or recovery-reference mutation.
- Governance-history projection into `main` or the integration branch.
- Modification of Integration A, Integration B, or their trees.
- Unrelated documentation changes.
- Repository cleanup or worktree cleanup.
- Deletion of the integration branch or worktree.
- Release publication or deployment.
- WO-004 activation.

## Required Promotion Report

Release & Integration must return a **WO-002/WO-003 Controlled Local-Main Promotion Report** containing:

- Every pre-promotion gate with exact observed values.
- Local, remote-tracking, and live remote `main` identities before promotion.
- Worktree inventory proving `main` was not checked out.
- Exact atomic command executed and its result.
- Local `main` commit and tree immediately after promotion.
- Exact two-commit ancestry and 21-path boundary evidence.
- CPython 3.11 focused, WO-003, and complete-suite results.
- Dependency-integrity, scoped Ruff, repository no-regression, and whitespace results.
- Clean and reproducible validation-environment evidence.
- Candidate, recovery, integration, unrelated-document, and remote-preservation evidence.
- Confirmation that no push or remote modification occurred.
- Whether recovery was required.
- If recovery occurred, the exact rollback command, result, and final local `main`.
- Final local `main`, remote-tracking `origin/main`, and live remote `main` identities.
- Any blocking, non-blocking, or deferred findings.
- A handoff to Documentation & Governance for final promotion disposition.

```text
Authorization status: AUTHORIZED — CONTROLLED LOCAL-MAIN FAST-FORWARD PROMOTION ONLY
Old local main: c137005b08c449a8e19f7734098865dd10181955
Authorized promotion target: f727d9f9f2b82b55f79e31008bb79b71477fbc84
Authorized target tree: 23f458c2d8a1576c8068aac3de0350dbc792d421
Promotion method: ATOMIC COMPARE-AND-SWAP UPDATE-REF FAST-FORWARD
Atomic old-value check required: YES — c137005b08c449a8e19f7734098865dd10181955
Merge commit authorized: NO
Local main modification authorized: YES — EXACT AUTHORIZED CAS UPDATE ONLY
Remote modification authorized: NO
Push authorized: NO
Rollback authority: YES — EXACT ATOMIC CAS TO PROTECTED BASE ON POST-PROMOTION FAILURE
WO-004 authorized: NO
Active owner: RELEASE & INTEGRATION ENGINEER
Required next report: WO-002/WO-003 CONTROLLED LOCAL-MAIN PROMOTION REPORT
```
