# Work Order WO-003: Runtime Execution-Conformance Validation

**Status:** CANDIDATE 1 REJECTED — CANDIDATE 2 CORRECTION AUTHORIZED
**Authority:** Engineering Director Decision implementing the Architecture Auditor's final reconciliation
**Active review owners:** QA & Verification; Architecture Auditor
**Date authorized:** 2026-07-29
**Date amended:** 2026-07-29
**Formal amendment:** `WO-GOV-003`
**Candidate ratification:** `WO-GOV-003B`
**Candidate 1 disposition:** `WO-GOV-003C`
**Architecture verdict:** AMEND WO-003 AND RECONSTRUCT
**Amendment review:** CONFIRMED; REQUIRED SEQUENCING CLARIFICATION RECORDED
**Authoritative base:** `4d1842087289336675d43d7cd650bd80f57b8c8d`
**Candidate tag:** `qa/wo-003-candidate-1`
**Tag object:** `cfbefaa046b043d2fa0b099a967f2936915499f8`
**Candidate SHA:** `7651fe4ac2fe242459d9864fb9256920fe3b2d9f`
**Candidate tree:** `fdbda901de7048f968d8d89efaa7f71a7aed8bcb`
**Implementation:** CANDIDATE 1 REJECTED; CORRECTION REQUIRED
**Candidate readiness:** CANDIDATE 2 NOT YET DESIGNATED
**QA & Verification:** CANDIDATE 1 QA ACCEPTED
**Architecture approval:** CANDIDATE 1 ARCHITECTURE REJECTED
**Documentation & Governance:** CANDIDATE 2 AUTHORITY RECORDED
**Next owner:** Release & Integration Engineer
**Governed by:** `governance/ENGINEERING_CHARTER.md`

---

## Objective

Deterministically verify that synchronous simulated execution preserves:

- Request identity.
- Interpreted mission.
- Selected agent and required capabilities.
- Generated workflow.
- Workflow order and completeness.
- Terminal lifecycle.
- Simulation boundary.

Expose structured conformance evidence through the canonical runtime, the existing `/execute-task` compatibility response, and the dashboard.

## Amended Authorization Basis

The Architecture Auditor completed the WO-003 Architectural Scope Reconciliation and issued:

```text
AMEND WO-003 AND RECONSTRUCT
```

The current branch must not be used as the WO-003 candidate because it contains product implementation, governance changes, superseded semantic corrections, WO-INF infrastructure, files outside the original authorization, and obsolete `RuntimeConformanceError` semantics.

The final runtime architecture is acceptable. Candidate composition and authorization require bounded reconstruction under this amended work order.

WO-002 remains closed. WO-003 does not reopen or expand WO-002.

## Formal Amendment Record

`WO-GOV-003 — Amend WO-003 reconstruction authority` formalizes the bounded reconstruction authority established by the Architecture Assessment.

This amendment:

- Fixes the authoritative reconstruction base.
- Enumerates the exact authorized paths required for the typed simulation boundary.
- Locks typed `conformance_failed` semantics without exception-based control flow.
- Excludes infrastructure ancestry, superseded corrections, unowned preserved work, and every unauthorized path.
- Defines the candidate evidence package required before independent review.
- Limits Release & Integration authority to manual bounded reconstruction.

This amendment does not approve implementation, release, integration, publication, or destructive repository operations.

## Authoritative Reconstruction Base

The exact and exclusive base for reconstructed WO-003 candidate 1 is:

```text
4d1842087289336675d43d7cd650bd80f57b8c8d
Close WO-002 canonical runtime hardening
```

This commit is the WO-002 closure commit and the direct parent of the initial WO-003 implementation.

The current branch and its current HEAD are not candidate bases.

## Authorized Final File List

Only the following paths may differ from the authoritative base in reconstructed WO-003 candidate 1.

### Core Runtime

- `aegis_os/core/cognitive_runtime.py`

### Execution

- `aegis_os/execution/conformance.py`
- `aegis_os/execution/models.py`
- `aegis_os/execution/execution_engine.py`

### API

- `aegis_os/api/app.py`

### Dashboard

- `aegis_os/api/static/dashboard.js`
- `aegis_os/api/templates/dashboard.html`

### Tests

- `tests/execution/test_conformance.py`
- `tests/execution/test_cancellation.py`
- `tests/execution/test_execution_engine.py`
- `tests/execution/test_models.py`
- `tests/core/test_cognitive_runtime.py`
- `tests/api/test_execute_task.py`
- `tests/api/test_execute_task_contract.py`
- `tests/api/test_dashboard.py`

### Documentation

- `docs/architecture/execution-engine.md`

### Compatibility-Only Files

No compatibility-only implementation file is authorized.

### Explicitly Excluded File

- `aegis_os/core/runtime_errors.py`

Any change outside the authorized final file list requires a separate authorization decision or a formal amendment before implementation.

## Locked Semantic Decisions

The following decisions are non-negotiable for WO-003 candidate 1:

1. `CognitiveRuntime` remains the sole orchestration owner.
2. Execution-conformance validation runs exactly once after simulated execution.
3. Analysis-only and gated operations report validation as `not_requested`.
4. Conformance validates contract fidelity only.
5. Conformance does not evaluate mission quality, governance, approval, learning, or real execution.
6. Failed conformance produces a valid `CanonicalRuntimeResult`.
7. Canonical runtime status for failed conformance is `conformance_failed`.
8. Normal execution-conformance failure is represented by the typed `conformance_failed` result and does not use exception-based control flow.
9. `RuntimeConformanceError` is superseded and must not be included in the reconstructed candidate.
10. Execution receipt outcome remains independent from conformance outcome.
11. Validation preserves checks, evidence, operation outcome, and request identity.
12. `/execute-task` returns:
    - HTTP 200 for passed conformance.
    - Structured HTTP 500 for failed conformance.
    - HTTP 422 for invalid input and non-ready execution.
13. Failed HTTP 500 responses preserve:
    - Analysis.
    - Execution receipt.
    - Validation.
    - Evidence.
    - Runtime status.
    - Request identifiers.
14. Request IDs match across:
    - Top-level result.
    - Analysis.
    - Execution.
    - Validation.
15. `/analyze-task` remains behaviorally unchanged.
16. `validation` and typed `execution_mode` are additive schema-version-1 fields.
17. Only simulated execution is authorized.

## Compatibility Guarantees

- `/analyze-task` behavior and response compatibility remain unchanged.
- `/execute-task` evolves additively under schema version 1.
- `validation` is an additive schema-version-1 field.
- Typed `execution_mode` is an additive schema-version-1 field.
- HTTP 422 remains limited to invalid input and non-ready execution.
- Passed conformance continues to return HTTP 200.
- Failed conformance returns structured HTTP 500 without discarding analysis, execution, validation evidence, runtime status, or correlated request identifiers.
- Execution outcome and conformance outcome remain separately represented.
- No new endpoint or full canonical-envelope publication is authorized.

## Explicit Non-Goals and Exclusions

WO-003 does not authorize:

- Governance execution.
- Evaluation or scoring.
- Learning.
- Memory or persistence.
- Resource resolution.
- Kernel/main convergence.
- Provider integration.
- Real execution.
- New endpoints.
- Full canonical-envelope publication.
- Cancellation API expansion.
- Infrastructure or CI changes.
- Repository cleanup.
- Generated-artifact removal.
- Branch-protection changes.
- Unowned stash content.
- Unrelated WO-002 changes.
- Unrelated product changes.
- Any path not specifically authorized by this amended work order.

Cancellation tests are authorized only as terminal-lifecycle validation.

## Historical Commit Controls

The following commits must not be replayed wholesale into reconstructed WO-003 candidate 1:

- `7723006`
- `c0db5b2`
- `2025aa0`
- `a62156e`
- `ead99d3`
- `e48070c`

Reconstruction may selectively reproduce final accepted behavior from:

- `5faf300`
- `78a4779`
- `098e925`
- `00f6a25`
- `e49243c`

Commit `4dd7c8e` may be used only for its additive API compatibility test concept.

These references are evidence sources, not authorization to cherry-pick or replay contaminated history.

All WO-INF infrastructure changes, superseded semantic corrections, unowned stash content, unrelated WO-002 or product changes, and changes outside the exact authorized path list are excluded from candidate 1.

## Reconstruction Authorization Record

The Release & Integration Engineer is authorized and required to:

1. Create a new bounded branch from exact base `4d1842087289336675d43d7cd650bd80f57b8c8d`.
2. Manually reconstruct the accepted final behavior.
3. Do not reconstruct by merging the current branch, copying its complete ancestry, applying preserved stashes, or transplanting unreviewed commits wholesale.
4. Ensure only amended authorized paths differ from the base.
5. Ensure infrastructure commit `ead99d3e15ffb920541c039c8c5cef1b8f4973a0` is not an ancestor.
6. Correct `docs/architecture/execution-engine.md` so it describes canonical-result failure rather than `RuntimeConformanceError`.
7. Validate the reconstructed implementation.
8. Freeze candidate 1 at an immutable SHA only after validation succeeds.

This reconstruction authority did not itself approve implementation, candidate readiness, release, integration, or closure. Candidate 1 was subsequently designated under separate release authority.

## Current Immutable Candidate

The separately authorized reconstruction and designation sequence produced:

```text
Tag: qa/wo-003-candidate-1
Tag object: cfbefaa046b043d2fa0b099a967f2936915499f8
Candidate SHA: 7651fe4ac2fe242459d9864fb9256920fe3b2d9f
Candidate tree: fdbda901de7048f968d8d89efaa7f71a7aed8bcb
Base SHA: 4d1842087289336675d43d7cd650bd80f57b8c8d
```

Candidate 1 is frozen. Its tag and target must not be moved, amended, recreated, deleted, or retargeted under this work order.

## Candidate 1 Ratification Record

`WO-GOV-003B` ratifies the existing annotated tag `qa/wo-003-candidate-1`; it does not replace, recreate, move, or alter the tag.

The following are immutable governance references:

- Annotated tag `qa/wo-003-candidate-1`.
- Tag object `cfbefaa046b043d2fa0b099a967f2936915499f8`.
- Peeled candidate commit `7651fe4ac2fe242459d9864fb9256920fe3b2d9f`.
- Candidate tree `fdbda901de7048f968d8d89efaa7f71a7aed8bcb`.
- Authoritative base `4d1842087289336675d43d7cd650bd80f57b8c8d`.

The existing tag annotation remains unchanged as historical evidence.

QA & Verification must evaluate the exact peeled candidate SHA `7651fe4ac2fe242459d9864fb9256920fe3b2d9f`. The Architecture Auditor must subsequently evaluate that same SHA. Any required correction must produce a new commit and Candidate 2. Candidate 1 must never move.

Ratification does not authorize push, merge, publication, modification of `main`, tag deletion or replacement, or any stash operation.

## Candidate 1 Final Disposition

Candidate 1 received:

```text
QA & Verification: CANDIDATE 1 QA ACCEPTED
Architecture Auditor: CANDIDATE 1 ARCHITECTURE REJECTED
```

Candidate 1 is rejected and remains immutable. Its QA acceptance remains part of the permanent historical record and does not override the Architecture rejection.

### Blocking Architecture Defect

Server-produced runtime invariant failures are raised as `ValueError` and subsequently mapped by the API to HTTP 422. This incorrectly represents internal runtime or validator contradictions as client request failures.

## Candidate 2 Correction Authority

Release & Integration is authorized to construct a Candidate 2 correction from immutable Candidate 1 commit:

```text
7651fe4ac2fe242459d9864fb9256920fe3b2d9f
```

Candidate 2 requires a new implementation commit SHA and a new candidate number. Candidate 1 and its annotated tag must never move.

### Required Candidate 2 Semantics

- Expected failed conformance remains a typed `CanonicalRuntimeResult` with status `conformance_failed` and structured HTTP 500.
- Genuine server-produced invariant failures use a dedicated invariant exception.
- The dedicated exception is defined within an already authorized implementation path.
- `RuntimeConformanceError` and `aegis_os/core/runtime_errors.py` remain prohibited.
- Internal invariant failures map intentionally to structured HTTP 500.
- `ValueError` and HTTP 422 remain reserved for genuine client-input and non-ready request conditions.
- Negative tests cover malformed validator output, request-ID mismatch, and operation-outcome mismatch.
- Architecture documentation distinguishes valid `conformance_failed` results from internal invariant faults.
- Server error responses use a stable classification without unnecessarily exposing internal details.

### Candidate 2 Maximum Correction Allowlist

Only paths actually required for the correction may change, up to this maximum allowlist:

- `aegis_os/core/cognitive_runtime.py`
- `aegis_os/api/app.py`
- `tests/core/test_cognitive_runtime.py`
- `tests/api/test_execute_task.py`
- `tests/api/test_execute_task_contract.py`
- `tests/execution/test_conformance.py`
- `docs/architecture/execution-engine.md`

Every non-allowlisted path remains prohibited.

### Candidate 2 Acceptance Criteria

Before designation:

1. The correction descends from immutable Candidate 1 SHA `7651fe4ac2fe242459d9864fb9256920fe3b2d9f`.
2. Only paths actually needed from the maximum correction allowlist differ from Candidate 1.
3. Expected conformance failure remains a typed `conformance_failed` result.
4. Genuine internal invariant faults use a dedicated invariant exception defined within an authorized path.
5. Internal invariant faults map to a stable structured HTTP 500 response without unnecessary internal detail.
6. `ValueError` and HTTP 422 remain reserved for client-input and non-ready conditions.
7. `RuntimeConformanceError` and `aegis_os/core/runtime_errors.py` are absent.
8. Negative tests cover malformed validator output, request-ID mismatch, and operation-outcome mismatch.
9. Architecture documentation distinguishes expected conformance failure from internal invariant faults.
10. Focused and full validation, including Python 3.11 evidence, pass against the exact proposed Candidate 2 HEAD.
11. The worktree is clean and exact path, commit-range, ancestry, and validation evidence are recorded.

Candidate 2 designation requires separate release authorization. After designation, QA & Verification and the Architecture Auditor must evaluate the same immutable Candidate 2 SHA.

### Candidate 2 Explicit Exclusions

- Moving, replacing, recreating, deleting, or amending Candidate 1 or its tag.
- `aegis_os/core/runtime_errors.py`.
- `RuntimeConformanceError`.
- Dashboard failed-response rendering changes.
- Status-derivation refactoring.
- Infrastructure, CI, dependencies, providers, kernel, persistence, learning, evaluation, or external execution.
- Every non-allowlisted path.
- Push, merge, publication, modification of `main`, shared rebase, stash application, or stash deletion.

The completed sequence was:

```text
bounded reconstruction
→ technical validation of exact implementation HEAD
→ immutable candidate designation
→ independent QA and Architecture review pending
```

Reconstruction and candidate designation must not be repeated.

## Acceptance Criteria

WO-003 is accepted only when:

1. The candidate descends from exact authoritative base `4d1842087289336675d43d7cd650bd80f57b8c8d`.
2. Only authorized final paths differ from the base.
3. Infrastructure commit `ead99d3e15ffb920541c039c8c5cef1b8f4973a0` is not an ancestor.
4. Conformance runs exactly once after simulated execution.
5. Analysis-only and execution-gated requests serialize validation as `not_requested`.
6. Validation is deterministic and side-effect free.
7. All defined checks return typed, serializable evidence.
8. Passed and failed conformance results are valid canonical outcomes.
9. Failed conformance uses canonical runtime status `conformance_failed`.
10. Normal failed conformance uses no exception-based control flow, and `RuntimeConformanceError` is absent from the candidate.
11. Failed conformance evidence survives the runtime and API boundaries.
12. Failed conformance returns structured HTTP 500, not HTTP 422.
13. Operation outcome remains distinct from conformance outcome.
14. Four-way request-ID correlation is enforced.
15. `/analyze-task` remains behaviorally unchanged.
16. `/execute-task` evolves only additively under schema version 1.
17. Dashboard terminology remains “Execution conformance” and does not imply evaluation, approval, governance, authorization, or mission success.
18. No explicit non-goal is introduced.
19. All required pre-freeze validation passes.
20. QA & Verification and the Architecture Auditor record verdicts, in that order, against the same immutable candidate SHA after designation.

## Required Pre-Freeze Evidence Gates

Before candidate designation, all of the following must pass against one exact proposed implementation HEAD SHA:

- Focused WO-003 tests.
- Complete pytest suite.
- Ruff lint.
- Ruff formatting check.
- Dependency-integrity validation.
- Pre-commit validation.
- `git diff --check`.
- Exact authorized-path inventory against the authoritative base.
- Commit-range and ancestry evidence from the authoritative base through the proposed implementation HEAD.
- Proof that `ead99d3e15ffb920541c039c8c5cef1b8f4973a0` is not an ancestor.
- Proof that `RuntimeConformanceError` is absent.
- Clean worktree.
- Exact proposed implementation HEAD SHA.
- Complete pre-freeze technical validation results tied to that exact proposed SHA.

### Focused Validation Coverage

Focused validation must cover:

- Every conformance check and mismatch.
- Passed and failed validation.
- Determinism.
- Exactly-once invocation.
- Completed, failed, and cancelled execution outcomes.
- Execution/conformance separation.
- Valid failed canonical result.
- Evidence serialization.
- Four-way request correlation.
- Structured HTTP 500.
- HTTP 200 and HTTP 422 compatibility.
- `/analyze-task` compatibility.
- Typed simulation boundary.
- Dashboard terminology and safe rendering.
- Absence of normal `RuntimeConformanceError`.

## Candidate Designation and Post-Freeze Review Gates

The governing sequence is:

1. Release & Integration reconstructs from the approved base.
2. Pre-freeze technical validation runs against an exact proposed implementation HEAD.
3. Under separate release authority, Release & Integration designates that unchanged SHA as an immutable candidate.
4. QA & Verification evaluates the immutable candidate and records candidate-specific evidence and a verdict.
5. The Architecture Auditor evaluates the same candidate SHA and records candidate-specific evidence and a verdict.
6. Any required correction creates a new implementation SHA and a new candidate number.
7. A designated candidate is never moved, amended, or retargeted.
8. Documentation & Governance may close WO-003 only after both independent verdicts reference the same immutable candidate SHA.

For the completed Candidate 1 review, the immutable reference was `qa/wo-003-candidate-1` at `7651fe4ac2fe242459d9864fb9256920fe3b2d9f`. Candidate 1 remains immutable and rejected.

### Post-Freeze Independent-Review Evidence

Closure requires:

- Immutable candidate tag or equivalent reference.
- Exact candidate SHA.
- QA & Verification verdict tied to that candidate SHA.
- Architecture Auditor verdict tied to the same candidate SHA.
- Confirmation that the candidate reference did not move during either review.

Candidate-specific QA and Architecture evidence is post-freeze evidence. It is not a pre-freeze technical-validation requirement.

## Governance Limitations

This amendment does not authorize:

- Pushing.
- Merging.
- Tagging.
- Rebasing shared branches.
- Deleting branches, stashes, or tags.
- Modifying `main`.
- Applying preserved work.
- Implementing infrastructure controls.

Release & Integration may prepare the bounded implementation and evidence package, but any immutable review-target operation that requires publication, tagging, integration, or another release mutation requires separate approval.

## Required Roles and Gates

```text
Documentation & Governance
→ amended reconstruction authorization recorded

Release & Integration Engineer
→ bounded reconstruction from the authoritative base
→ pre-freeze technical validation against an exact implementation HEAD SHA

Separately authorized Release & Integration action
→ designate that unchanged SHA as immutable candidate 1

QA & Verification
→ candidate-specific evidence and independent verdict against candidate 1

Architecture Auditor
→ candidate-specific evidence and independent verdict against the same candidate SHA

Documentation & Governance
→ closure only after all evidence and approvals are recorded
```

## Roadmap Placement

WO-003 must be completed before kernel/main convergence. Kernel/main convergence remains the next Phase I slice after WO-003 closure and is not opened or authorized by this amendment.

## Traceability

This amended work order is linked through `governance/TRACEABILITY.md` to:

- WO-002 closure at the authoritative reconstruction base.
- The original WO-003 authorization.
- The Architecture Auditor's final scope reconciliation.
- The Engineering Director's reconstruction amendment assignment.
- The frozen Candidate 1 identity and independent-review evidence when produced.

## Governance Commit Reconciliation

The two amendment commits have distinct, cumulative roles:

| Commit | Relationship and content | Governance disposition |
|---|---|---|
| `39b059ebdc2de8b87372108ca15887d6f6a06b91` | Initial reconstruction-scope amendment. Recorded the authoritative base, expanded exact path scope, semantic locks, exclusions, reconstruction instructions, and evidence gates. | Retained as the historical foundation of the amended authorization. |
| `43899da52c3d78399f6efb4a3b0c9418c58aa8d5` | Direct child of `39b059e`; formally identified `WO-GOV-003` and tightened non-exception `conformance_failed` semantics, stash and unrelated-work exclusions, candidate evidence, and release limitations. | Authoritative formal WO-GOV-003 amendment record. |

`43899da` follows and supersedes `39b059e` where their wording differs; it does not erase the historical amendment. Both commits remain referenced for complete traceability.

## Current Gate

```text
CANDIDATE 1 REJECTED — CANDIDATE 2 CORRECTION AUTHORIZED
```

WO-003 is not closed, integrated, merged, or released. Candidate 1 QA acceptance and Architecture rejection are final historical verdicts for Candidate 1. Candidate 2 has not been designated or independently reviewed.

## Stop Condition

Hand off to Release & Integration for the bounded Candidate 2 correction. Do not designate Candidate 2 without separate release authorization.

Do not move, amend, recreate, delete, or retarget Candidate 1. Do not close WO-003 until QA & Verification and the Architecture Auditor approve the same immutable Candidate 2 SHA and required Python 3.11 evidence is recorded.
