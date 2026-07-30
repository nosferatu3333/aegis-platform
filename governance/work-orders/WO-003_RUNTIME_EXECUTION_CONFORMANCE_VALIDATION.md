# Work Order WO-003: Runtime Execution-Conformance Validation

**Status:** AUTHORIZED — AMENDED; RECONSTRUCTION REQUIRED
**Authority:** Engineering Director Decision implementing the Architecture Auditor's final reconciliation
**Accountable role:** Release & Integration Engineer
**Date authorized:** 2026-07-29
**Date amended:** 2026-07-29
**Formal amendment:** `WO-GOV-003`
**Architecture verdict:** AMEND WO-003 AND RECONSTRUCT
**Amendment review:** CONFIRMED; REQUIRED SEQUENCING CLARIFICATION RECORDED
**Authoritative base:** `4d1842087289336675d43d7cd650bd80f57b8c8d`
**Implementation:** NOT ACCEPTED; BOUNDED RECONSTRUCTION REQUIRED
**Candidate readiness:** NOT READY
**QA & Verification:** PENDING
**Architecture approval:** PENDING
**Documentation & Governance:** AMENDMENT RECORDED
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

This record authorizes bounded reconstruction. It does not approve implementation, candidate readiness, release, integration, or closure.

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

After pre-freeze technical validation passes:

1. Separate release authority must designate the exact validated implementation SHA as immutable candidate 1 without changing its contents.
2. QA & Verification evaluates candidate 1 and records candidate-specific evidence and a verdict against the designated SHA.
3. The Architecture Auditor evaluates the same candidate SHA after QA and records candidate-specific evidence and a verdict.
4. Any correction creates a new implementation SHA and a new candidate number.
5. Candidate 1 is never moved, amended, or reused for corrected contents.
6. Documentation & Governance may close WO-003 only after both independent verdicts apply to the same immutable candidate SHA.

Candidate designation, publication, or tagging remains subject to separately approved release controls.

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
- The bounded reconstruction and immutable candidate evidence when produced.

## Current Gate

```text
AUTHORIZED — AMENDED; RECONSTRUCTION REQUIRED
```

WO-003 is not implemented, candidate-ready, QA passed, Architecture approved, closed, or integrated.

## Stop Condition

Stop after the amended authorization is recorded and handed to the Release & Integration Engineer.

During reconstruction, stop and escalate before changing an unauthorized path, introducing an explicit non-goal, carrying excluded history into the candidate, or freezing a candidate without all pre-freeze evidence.
