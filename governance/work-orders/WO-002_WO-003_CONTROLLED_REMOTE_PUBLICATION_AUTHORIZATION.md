# WO-002/WO-003 Controlled Remote-Publication Authorization

**Authorization status:** AUTHORIZED — EXACT LEASE-GUARDED REMOTE-MAIN PUBLICATION ONLY
**Date authorized:** 2026-07-30
**Remote:** `https://github.com/nosferatu3333/aegis-platform.git`
**Expected old remote `main`:** `c137005b08c449a8e19f7734098865dd10181955`
**Authorized publication source:** `f727d9f9f2b82b55f79e31008bb79b71477fbc84`
**Authorized publication tree:** `23f458c2d8a1576c8068aac3de0350dbc792d421`
**Authorized destination:** `refs/heads/main`
**Local-promotion disposition:** `680c9950215a9a58f58f355f3b490d4aaf2b5264`
**Active owner:** Release & Integration Engineer
**Release publication:** NOT AUTHORIZED
**WO-004:** NOT AUTHORIZED
**Execution status:** COMPLETED — PASS; EXACTLY ONE REMOTE REFERENCE UPDATED
**Final publication disposition:** [`WO-002_WO-003_FINAL_REMOTE_PUBLICATION_GOVERNANCE_DISPOSITION.md`](WO-002_WO-003_FINAL_REMOTE_PUBLICATION_GOVERNANCE_DISPOSITION.md)

---

## Purpose

This authorization permits Release & Integration to publish the exact accepted local `main` object to remote `refs/heads/main` through one explicit old-value-guarded push.

Authority is conditional on every pre-publication identity, ancestry, remote, reference, policy, and preservation gate. No other local or remote reference may be included.

This authorization publishes Git history only. It does not publish a release, deploy the platform, clean local state, or activate WO-004.

## Exact Remote and Publication Identities

| Control | Exact identity |
|---|---|
| Remote name | `origin` |
| Remote URL | `https://github.com/nosferatu3333/aegis-platform.git` |
| Expected old remote `main` | `c137005b08c449a8e19f7734098865dd10181955` |
| Local publication source | `f727d9f9f2b82b55f79e31008bb79b71477fbc84` |
| Source tree | `23f458c2d8a1576c8068aac3de0350dbc792d421` |
| Remote destination | `refs/heads/main` |
| Integration A | `fb0364d1b4e0a27953ea7d683a786193d6e61c48` |
| Protected base | `c137005b08c449a8e19f7734098865dd10181955` |

The only authorized update is:

```text
refs/heads/main
c137005b08c449a8e19f7734098865dd10181955
→ f727d9f9f2b82b55f79e31008bb79b71477fbc84
```

## Mandatory Pre-Publication Gates

Immediately before executing the push, Release & Integration must independently verify:

1. Local `refs/heads/main` equals exact source `f727d9f9f2b82b55f79e31008bb79b71477fbc84`.
2. Local `main^{tree}` equals `23f458c2d8a1576c8068aac3de0350dbc792d421`.
3. Integration A remains the direct, sole child of protected base `c137005b08c449a8e19f7734098865dd10181955`.
4. Integration B remains the direct, sole child of Integration A.
5. The protected-base-to-source range contains exactly two commits.
6. Live remote `refs/heads/main` equals exact expected old SHA `c137005b08c449a8e19f7734098865dd10181955`.
7. Local remote-tracking `refs/remotes/origin/main` equals the same live remote SHA.
8. Remote name `origin` resolves exactly to `https://github.com/nosferatu3333/aegis-platform.git`.
9. The expected old remote commit is an ancestor of the exact publication source, making the update a strict fast-forward.
10. Candidate, recovery, and integration references remain unchanged.
11. The final source boundary remains exactly 21 paths with zero unauthorized paths.
12. No tag, wildcard, additional branch, or additional refspec is present in the proposed command.
13. The unrelated documentation retains its exact preserved hashes and remains outside the publication environment.
14. The configured credentials identify an authorized publisher and are unambiguous.
15. Applicable branch-protection and remote-policy requirements are understood and have not been weakened or bypassed.
16. No local, remote-tracking, live remote, repository, or credential identity has diverged.

The protected references are:

| Reference | Required object or target |
|---|---|
| Candidate 1 tag object | `cfbefaa046b043d2fa0b099a967f2936915499f8` |
| Candidate 1 commit | `7651fe4ac2fe242459d9864fb9256920fe3b2d9f` |
| Candidate 2 tag object | `3b674e57b18568fe1e2a4509f8448ffeaff647ee` |
| Candidate 2 commit | `eee135547a768c3cad95c1e2e5342e9203620463` |
| Recovery tag object | `9406fc75ecd6ddc5ef45adeff4042587dfdb2bf8` |
| Recovery target | `c137005b08c449a8e19f7734098865dd10181955` |
| Integration branch | `f727d9f9f2b82b55f79e31008bb79b71477fbc84` |

The preserved unrelated-document hashes are:

| Path | Required SHA-256 |
|---|---|
| `docs/AEGIS_CURRENT_STATE_DIAGNOSTIC.md` | `085BF9CB521B5DF6E98FADCE99A8E495A6A80EE3C89853C55BFFBCDA2CBF79AA` |
| `docs/audits/IMPLEMENTATION_GAP_ANALYSIS.md` | `DA2FA2FDAF0F6BE0718DF5505B7D5825B85DEBC54857CB79C62C564CA7C21806` |

Any mismatch or ambiguity is a stop condition.

## Authorized Push Command

After every pre-publication gate passes, the only authorized mutating command is:

```powershell
git push --porcelain `
  --force-with-lease=refs/heads/main:c137005b08c449a8e19f7734098865dd10181955 `
  origin `
  f727d9f9f2b82b55f79e31008bb79b71477fbc84:refs/heads/main
```

The command requirements are:

- The source is an explicit immutable commit SHA.
- The destination is exact remote `refs/heads/main`.
- The lease names the exact expected old remote SHA.
- The refspec contains exactly one source and one destination.
- The update is independently proven to be a strict fast-forward before execution.
- `--force-with-lease` serves only as the atomic old-value guard; it does not authorize non-fast-forward publication.
- Porcelain output is required for exact evidence.

No substitution, abbreviation, unresolved branch source, wildcard, additional refspec, or changed lease is authorized.

## Explicitly Excluded References

The push must not include:

- Any `refs/tags/*` reference.
- Candidate 1 or Candidate 2 tags.
- The recovery tag.
- `refs/heads/integration/wo-002-wo-003-c137005b`.
- Any governance branch or governance commit reference.
- Any WO-003 reconstruction or correction branch.
- Any Infrastructure or CI branch.
- Any branch other than remote `refs/heads/main`.
- Any deletion refspec.
- Any implicitly followed tag.

Options including `--tags`, `--follow-tags`, `--all`, `--mirror`, wildcard refspecs, and deletion refspecs are prohibited.

## Post-Publication Verification

Immediately after a reported successful push, Release & Integration must verify:

1. Porcelain output identifies exactly one updated destination: `refs/heads/main`.
2. Live remote `refs/heads/main` equals exact published SHA `f727d9f9f2b82b55f79e31008bb79b71477fbc84`.
3. Local remote-tracking `refs/remotes/origin/main` equals the same published SHA.
4. Remote `main` resolves to tree `23f458c2d8a1576c8068aac3de0350dbc792d421`.
5. The remote update contains exactly Integration A and Integration B after the old remote base.
6. The update remains a strict fast-forward with the exact accepted two-commit ancestry.
7. A before-and-after remote-reference inventory differs only at `refs/heads/main`.
8. No candidate, integration, recovery, governance, Infrastructure, CI, unrelated branch, or tag was published.
9. Local `main`, Integration A, Integration B, candidate references, and recovery references remain unchanged.
10. Unrelated documentation hashes remain unchanged.
11. No release was published or deployed.
12. WO-004 remains inactive.

Remote-reference verification must use live remote evidence, not only the local remote-tracking reference.

## Stop Conditions

Stop without publication if:

- Any pre-publication gate fails.
- Live remote `main` cannot be confirmed at the exact expected old SHA.
- Remote-tracking and live remote `main` disagree.
- The remote URL, repository identity, credentials, or publisher identity is ambiguous.
- Strict fast-forward ancestry cannot be proven.
- The exact lease cannot be used.
- Branch protection or remote policy rejects or conflicts with the requested operation.
- The command would include another ref, tag, wildcard, branch, or implicit publication.
- Any accepted or protected local object has changed.
- Any unrelated-document hash has changed.

If the push is rejected or fails:

1. Record the exact command, porcelain output, exit status, and observed live remote state.
2. Stop.
3. Do not weaken branch protection, alter credentials, change the lease, use ordinary force, add a merge, or retry through another method.
4. Return the failure evidence to Documentation & Governance.

## Unexpected Post-Publication State

No automatic remote rollback is authorized.

If push output reports success but any post-publication verification is unexpected:

1. Stop all further remote operations.
2. Capture live remote and local reference inventories.
3. Preserve local commits, branches, tags, worktrees, and governance evidence.
4. Do not force-push, delete, revert, reset, retag, or attempt another publication.
5. Escalate immediately for a separate recovery decision.

## Explicit Restrictions

This authorization does not permit:

- Publication of any tag or other branch.
- Publication of governance history.
- Ordinary `--force` or a push without the exact lease.
- Non-fast-forward publication.
- Rebase, squash, amendment, cherry-pick, recreation, or content modification.
- Remote reference deletion.
- Weakening or bypassing GitHub protection.
- Credential substitution or use of an ambiguous publisher identity.
- Release publication, deployment, or announcement.
- Local branch, worktree, tag, recovery, or candidate cleanup.
- Modification of unrelated documentation.
- WO-004 activation.

## Required Publication Report

Release & Integration must return a **WO-002/WO-003 Controlled Remote-Publication Report** containing:

- Exact authorization and governance-disposition identities.
- Every pre-publication gate with exact observed values.
- Remote name, URL, credential identity, and applicable protection status.
- Local source SHA and tree.
- Live and remote-tracking `main` before publication.
- Strict fast-forward and exact two-commit ancestry evidence.
- Complete before-publication remote-reference inventory.
- Exact push command, porcelain output, exit status, and timestamp.
- Live and remote-tracking `main` after publication.
- Remote `main` tree and two-commit range evidence.
- Complete after-publication remote-reference inventory and exact diff.
- Confirmation that only `refs/heads/main` changed.
- Candidate, recovery, integration, local-main, and unrelated-document preservation evidence.
- Confirmation that no tag, other branch, governance history, release, or WO-004 state was published.
- Any blocking, non-blocking, or deferred findings.
- Handoff to Documentation & Governance for final remote-publication disposition.

```text
Authorization status: AUTHORIZED — EXACT LEASE-GUARDED REMOTE-MAIN PUBLICATION ONLY
Remote: https://github.com/nosferatu3333/aegis-platform.git
Expected old remote main: c137005b08c449a8e19f7734098865dd10181955
Authorized publication source: f727d9f9f2b82b55f79e31008bb79b71477fbc84
Authorized publication tree: 23f458c2d8a1576c8068aac3de0350dbc792d421
Authorized destination: refs/heads/main
Strict fast-forward required: YES
Exact lease required: YES — refs/heads/main:c137005b08c449a8e19f7734098865dd10181955
Tags authorized: NO
Other branches authorized: NO
Ordinary force authorized: NO
Remote rollback authorized: NO
Release publication authorized: NO
WO-004 authorized: NO
Active owner: RELEASE & INTEGRATION ENGINEER
Required next report: WO-002/WO-003 CONTROLLED REMOTE-PUBLICATION REPORT
```
