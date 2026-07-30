# WO-002/WO-003 Bounded Integration Authorization

**Authorization status:** AUTHORIZED — LOCAL ISOLATED COMPOSITION AND VALIDATION ONLY
**Date authorized:** 2026-07-30
**Architecture verdict:** APPROVE DEPENDENCY-AWARE TWO-STAGE INTEGRATION, SUBJECT TO EXPLICIT INTEGRATION AUTHORIZATION AND STAGE-GATED VALIDATION
**Authorized owner:** Release & Integration Engineer
**Governance owner:** Documentation & Governance
**WO-002 status:** CLOSED
**WO-003 status:** CLOSED — CANDIDATE 2 ACCEPTED
**WO-004 status:** NOT ACTIVATED
**Ruff baseline amendment:** [`WO-002_WO-003_BOUNDED_INTEGRATION_RUFF_BASELINE_AMENDMENT.md`](WO-002_WO-003_BOUNDED_INTEGRATION_RUFF_BASELINE_AMENDMENT.md)
**Python-only Ruff target amendment:** [`WO-002_WO-003_BOUNDED_INTEGRATION_PYTHON_ONLY_RUFF_TARGET_AMENDMENT.md`](WO-002_WO-003_BOUNDED_INTEGRATION_PYTHON_ONLY_RUFF_TARGET_AMENDMENT.md)

---

## Purpose

This authorization permits Release & Integration to construct and validate a local, isolated, dependency-aware composition of the closed WO-002 and WO-003 scopes. The composition must use exact source blobs, two separately reviewable commits, and the stage gates defined here.

This authorization does not promote the resulting composition. It does not authorize modification of `main`, push, publication, release, or WO-004 activation.

## Authoritative Identities

| Control | Exact identity |
|---|---|
| Integration base | `c137005b08c449a8e19f7734098865dd10181955` |
| WO-002 authoritative source | `4d1842087289336675d43d7cd650bd80f57b8c8d` |
| WO-003 Candidate 2 tag | `qa/wo-003-candidate-2` |
| WO-003 Candidate 2 tag object | `3b674e57b18568fe1e2a4509f8448ffeaff647ee` |
| WO-003 Candidate 2 commit | `eee135547a768c3cad95c1e2e5342e9203620463` |
| WO-003 Candidate 2 tree | `ee0e3c0b0b95547b1006babc50d9cac419a96686` |
| WO-003 governance closure | `655045c33ecea736fde25e0ba46f865d175cba7d` |

Release & Integration must verify these identities before creating any reference, branch, worktree, or commit. Any mismatch is a stop condition.

## Authorized Integration Model

The only authorized composition is:

```text
integration base c137005b08c449a8e19f7734098865dd10181955
→ Integration A: exact nine-path WO-002 foundation
→ Stage 1 validation
→ Integration B: exact sixteen-path WO-003 Candidate 2 overlay
→ Stage 2 validation
→ immutable reported local integration SHA
→ independent integration-specific QA and Architecture review
```

The two source lineages must not be merged, replayed, or transplanted wholesale. Existing commits may be inspected only as evidence. The resulting local history must consist of the integration base followed by exactly two new bounded integration commits.

## Stage 1 — WO-002 Bounded Foundation

Integration A must source the exact blob for each path below from commit `4d1842087289336675d43d7cd650bd80f57b8c8d`:

```text
aegis_benchmark/runner.py
aegis_os/api/__init__.py
aegis_os/api/app.py
aegis_os/core/cognitive_runtime.py
aegis_os/pipeline/composition.py
tests/api/test_execute_task.py
tests/benchmark/test_runner.py
tests/core/__init__.py
tests/core/test_cognitive_runtime.py
```

Integration A must change exactly these nine paths relative to the integration base. Its parent must be exact base `c137005b08c449a8e19f7734098865dd10181955`. Every resulting path blob must match the corresponding blob at the WO-002 source.

## Stage 2 — WO-003 Candidate 2 Overlay

After Stage 1 passes, Integration B must overlay the exact blob for each path below from Candidate 2 commit `eee135547a768c3cad95c1e2e5342e9203620463`:

```text
aegis_os/api/app.py
aegis_os/api/static/dashboard.js
aegis_os/api/templates/dashboard.html
aegis_os/core/cognitive_runtime.py
aegis_os/execution/conformance.py
aegis_os/execution/execution_engine.py
aegis_os/execution/models.py
docs/architecture/execution-engine.md
tests/api/test_dashboard.py
tests/api/test_execute_task.py
tests/api/test_execute_task_contract.py
tests/core/test_cognitive_runtime.py
tests/execution/test_cancellation.py
tests/execution/test_conformance.py
tests/execution/test_execution_engine.py
tests/execution/test_models.py
```

Integration B must change exactly these sixteen paths relative to Integration A. Every resulting Stage 2 path blob must match the corresponding blob at Candidate 2. No semantic adaptation is authorized.

## Final 21-Path Boundary

The final composition may differ from integration base `c137005b08c449a8e19f7734098865dd10181955` in exactly these 21 unique product, test, and architecture-document paths:

```text
aegis_benchmark/runner.py
aegis_os/api/__init__.py
aegis_os/api/app.py
aegis_os/api/static/dashboard.js
aegis_os/api/templates/dashboard.html
aegis_os/core/cognitive_runtime.py
aegis_os/execution/conformance.py
aegis_os/execution/execution_engine.py
aegis_os/execution/models.py
aegis_os/pipeline/composition.py
docs/architecture/execution-engine.md
tests/api/test_dashboard.py
tests/api/test_execute_task.py
tests/api/test_execute_task_contract.py
tests/benchmark/test_runner.py
tests/core/__init__.py
tests/core/test_cognitive_runtime.py
tests/execution/test_cancellation.py
tests/execution/test_conformance.py
tests/execution/test_execution_engine.py
tests/execution/test_models.py
```

The four paths shared by both stages are:

```text
aegis_os/api/app.py
aegis_os/core/cognitive_runtime.py
tests/api/test_execute_task.py
tests/core/test_cognitive_runtime.py
```

Their final blobs must come from WO-003 Candidate 2.

## Explicit Exclusions

The integration must not replay, merge, cherry-pick, or otherwise transplant:

```text
cac8a9ff8dc3b3c839d9aea3ec365087734a389f
9a7cc443b569fe39aed13ae0446701228e5f9db6
3cd3911eefb7a81fe6615e0820a35474f369ab69
```

The following are also excluded:

- The remaining 91 unrelated paths identified by the dependency assessment.
- Every path outside the exact 21-path boundary.
- Workspace tooling and infrastructure.
- Repository-wide normalization.
- Rejected or alternate WO-003 lineages.
- WO-INF implementation history.
- Kernel, learning, memory, provider, persistence, or external-execution expansion.
- Unrelated documentation changes.
- `docs/AEGIS_CURRENT_STATE_DIAGNOSTIC.md`.
- `docs/audits/IMPLEMENTATION_GAP_ANALYSIS.md`.
- Candidate or governance lineage merges.
- Semantic adaptation between the two exact source states.

## Governance Projection Rule

The no-source-governance-blob projection rule is authoritative:

1. Do not copy or overwrite historical `governance/TRACEABILITY.md` from either source tree.
2. Do not copy any governance path into Integration A or Integration B.
3. Do not merge governance closure commit `655045c33ecea736fde25e0ba46f865d175cba7d` or its lineage.
4. Keep the integration composition limited to the exact 21-path boundary.
5. After integration-specific QA and Architecture review, Documentation & Governance may record the integration disposition only under separate governance authority.

No governance path is part of the integration candidate.

## Isolation and Preservation Authority

### Recovery reference

Release & Integration is authorized to create exactly one local annotated recovery tag:

```text
refs/tags/recovery/pre-wo-002-wo-003-integration-c137005b
```

The tag must point to exact current `main` commit `c137005b08c449a8e19f7734098865dd10181955`. Its annotation must identify this authorization and the protected base. Once created, it is an immutable local recovery reference. Moving, replacing, deleting, or pushing it is not authorized.

### Integration branch

Release & Integration is authorized to create exactly one new local branch:

```text
integration/wo-002-wo-003-c137005b
```

The branch must be created from exact base `c137005b08c449a8e19f7734098865dd10181955`.

### Integration worktree

Release & Integration is authorized to create one separate clean worktree at:

```text
C:\Users\Woolis Shop\Projects\aegis-platform-int-wo-002-wo-003-c137005b
```

The branch, recovery tag, and worktree names were verified unused when this authorization was recorded. If any name or path is occupied when execution begins, stop and report the collision. Do not overwrite, reuse, delete, or silently substitute another name.

The current worktree and all existing worktrees must remain untouched. In particular, preserve the two excluded uncommitted documentation paths without staging, restoring, formatting, stashing, cleaning, or copying them.

## Local Commit Authority

Exactly two new local commits are authorized on the integration branch:

1. **Integration A — bounded WO-002 foundation:** exactly the nine Stage 1 paths.
2. **Integration B — exact WO-003 Candidate 2 overlay:** exactly the sixteen Stage 2 paths, with Integration A as its parent.

No merge commit, cherry-pick, rebase, source-lineage replay, fixup commit, governance commit, or third integration commit is authorized. If a correction is required, stop and request amended authority.

## Validation Environment

Both stages require CPython 3.11. The final report must record the exact Python 3.11 patch version and interpreter identity used.

Ruff must run in check-only mode using the `pyproject.toml` configuration already tracked at integration base `c137005b08c449a8e19f7734098865dd10181955`. The configuration must not be replaced or modified, and formatting must not rewrite files.

Repository-wide Ruff is governed by the bounded no-regression policy in the [Ruff Baseline Amendment](WO-002_WO-003_BOUNDED_INTEGRATION_RUFF_BASELINE_AMENDMENT.md). The protected base and each evaluated integration stage must produce the same exact three-diagnostic inherited baseline. All authorized Python integration paths must pass direct Ruff lint and format-check. The three non-Python boundary paths are governed by the [Python-Only Ruff Target Amendment](WO-002_WO-003_BOUNDED_INTEGRATION_PYTHON_ONLY_RUFF_TARGET_AMENDMENT.md).

## Stage 1 Validation Gates

Before Stage 2 begins, Release & Integration must prove:

1. Integration A has exact parent `c137005b08c449a8e19f7734098865dd10181955`.
2. Its delta contains exactly the nine authorized Stage 1 paths.
3. Every Stage 1 blob matches `4d1842087289336675d43d7cd650bd80f57b8c8d`.
4. `create_default_runtime` imports successfully.
5. Runtime and API smoke tests pass.
6. Benchmark delegation passes.
7. Focused runtime, API, and benchmark tests pass.
8. The full repository test suite passes.
9. Dependency integrity passes.
10. Repository-wide Ruff output exactly matches the inherited protected-base diagnostic set under the Ruff Baseline Amendment.
11. Direct Ruff lint against all nine Stage 1 paths passes.
12. Ruff format-check against all nine Stage 1 paths passes.
13. No unrelated path or incidental tracked change is present.
14. The integration worktree is clean after validation.

A failed or incomplete Stage 1 gate prohibits Stage 2.

## Stage 2 Validation Gates

After Integration B is created, Release & Integration must prove:

1. Integration B has Integration A as its sole parent.
2. Its delta contains exactly the sixteen authorized Stage 2 paths.
3. Every Stage 2 blob matches Candidate 2 commit `eee135547a768c3cad95c1e2e5342e9203620463`.
4. The five Stage 1-only paths retain their WO-002 source blobs.
5. The final base-to-integration delta contains exactly the 21 authorized paths.
6. Focused validation passes.
7. Complete WO-003 validation passes.
8. The full repository test suite passes.
9. Dependency integrity passes.
10. Direct Ruff lint against the final exact 18-path Python manifest passes.
11. Ruff format-check against the final exact 18-path Python manifest passes.
12. Repository-wide Ruff output exactly matches the inherited protected-base diagnostic set, with no violation in an authorized path.
13. Candidate 1 and Candidate 2 tags and commits remain unchanged.
14. The prohibited commits and source/governance lineages are absent from integration ancestry.
15. No incidental tracked change remains.
16. The integration worktree is clean after validation.

## Post-Composition Gate

The final local Integration B commit SHA is a new composition and is not an approved promotion target merely because stage validation passes.

After successful composition:

1. Release & Integration must stop and return the required composition report.
2. QA & Verification must independently review the exact reported integration SHA.
3. The Architecture Auditor must review that same SHA and verify that no semantic adaptation or scope expansion was introduced.
4. Documentation & Governance may record the integration disposition only under separate governance authority.
5. A separate explicit promotion authorization is required before any modification of `main` or push.

The integration branch must remain fixed at the reported SHA during independent review. Creating an integration tag or other review reference is not authorized by this record.

## Stop Conditions

Stop immediately and report without broadening scope if:

- Any authoritative identity does not match.
- The recovery tag, branch name, or worktree path is already occupied.
- A source blob is absent or fails to match.
- A stage contains an unauthorized path.
- A required validation gate fails or cannot be executed on CPython 3.11.
- A repository-wide Ruff diagnostic differs from the exact inherited baseline or an authorized Python path fails scoped Ruff validation.
- The authorized Ruff configuration would need modification.
- Composition requires semantic adaptation, conflict resolution, or a third commit.
- A candidate tag or source reference changes.
- An excluded commit or lineage appears in ancestry.
- The current worktree or an existing worktree would need modification.
- `main`, remote state, or preserved uncommitted work would be affected.

No failed stage may be promoted or represented as accepted.

## Rollback Procedure

Because all work occurs on a new local branch in a separate worktree and `main` remains untouched, rollback is non-promotional:

1. Stop at the last completed authorized stage.
2. Record the branch, worktree, recovery reference, commit SHA, exact diff, and failure evidence.
3. Leave `main`, existing branches, existing worktrees, candidate references, and preserved uncommitted work unchanged.
4. Preserve the local integration branch, worktree, commits, and recovery tag for audit.
5. Do not reset, delete, clean, rebase, amend, or reuse those objects without separate cleanup or correction authorization.

## Explicitly Prohibited Actions

This authorization does not permit:

- Modifying, merging into, rebasing, or resetting `main`.
- Pushing any branch, tag, commit, or reference.
- Publishing or releasing the composition.
- Activating WO-004 or beginning kernel/main convergence.
- Merging either source lineage or the governance closure lineage.
- Cherry-picking the excluded commits or any unreviewed commit.
- Creating any commit beyond Integration A and Integration B.
- Modifying the exact source blobs after projection.
- Remediating inherited Ruff debt or modifying its two base paths.
- Modifying Ruff configuration, dependencies, or Infrastructure policy.
- Editing or adding a governance path to the integration branch.
- Modifying, moving, replacing, or deleting candidate tags.
- Stashing, cleaning, restoring, formatting, staging, or committing preserved unrelated work.
- Deleting the integration branch, worktree, commits, or recovery tag.

## Required Final Report

Release & Integration must return a **WO-002/WO-003 Bounded Integration Composition Report** containing:

- Exact integration base, WO-002 source, Candidate 2 tag object, commit, and tree.
- Recovery tag name, target, and created tag object.
- Integration branch name and worktree path.
- Integration A SHA, parent, exact nine-path inventory, and per-path source-blob proof.
- Stage 1 CPython 3.11 environment, commands, results, and clean-state evidence.
- Stage 1 scoped Ruff results and exact protected-base no-regression comparison evidence.
- Integration B/final integration SHA, parent, exact sixteen-path inventory, and per-path Candidate 2 blob proof.
- Exact final 21-path base delta.
- Commit-range and ancestry evidence proving only the base and two integration commits compose the local integration history.
- Proof that excluded commits, source lineages, governance paths, and incidental changes are absent.
- Stage 2 CPython 3.11 environment, commands, results, and clean-state evidence.
- Stage 2 18-path Python Ruff results, three-path non-Python verification evidence, and exact repository-wide no-regression comparison evidence.
- Candidate tag immutability confirmation.
- Confirmation that the preserved documentation changes were untouched.
- Confirmation that `main` and remote state were unchanged and no push occurred.
- Any blocking, non-blocking, or deferred findings.
- Exact immutable integration SHA proposed for independent QA and Architecture review.

```text
Authorization status: AUTHORIZED — LOCAL ISOLATED COMPOSITION AND VALIDATION ONLY
Integration base: c137005b08c449a8e19f7734098865dd10181955
WO-002 source: 4d1842087289336675d43d7cd650bd80f57b8c8d
WO-003 source: qa/wo-003-candidate-2 at eee135547a768c3cad95c1e2e5342e9203620463
Stage 1 paths: 9
Stage 2 paths: 16
Final unique path boundary: 21
Governance projection: NO SOURCE GOVERNANCE BLOBS; SEPARATE POST-REVIEW GOVERNANCE AUTHORITY REQUIRED
Recovery reference authorized: YES — refs/tags/recovery/pre-wo-002-wo-003-integration-c137005b
Integration branch authorized: YES — integration/wo-002-wo-003-c137005b
Integration worktree authorized: YES — C:\Users\Woolis Shop\Projects\aegis-platform-int-wo-002-wo-003-c137005b
Local commits authorized: EXACTLY TWO — INTEGRATION A AND INTEGRATION B
Main modification authorized: NO
Push authorized: NO
WO-004 authorized: NO
Active owner: RELEASE & INTEGRATION ENGINEER
Required next report: WO-002/WO-003 BOUNDED INTEGRATION COMPOSITION REPORT
```
