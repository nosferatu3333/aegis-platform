# Work Order WO-004: Kernel Canonical Runtime Convergence

**Status:** CLOSED - PUBLISHED TO MAIN
**Authority:** Product Owner / Founder activation decision, recorded by Documentation & Governance
**Date authorized:** 2026-07-31
**Authoritative base:** `8514de1f4e1bafb73748ec74a9b29e8b2f83d952`
**Implementation owner:** Implementation Engineer
**Required review owners:** QA & Verification; Architecture Auditor; Documentation & Governance
**Integration authority:** EXECUTED - COMPLETE
**Remote-publication authority:** EXECUTED - COMPLETE
**Governed by:** `governance/ENGINEERING_CHARTER.md`

---

## Objective

Converge the application entry path onto the canonical `CognitiveRuntime` while preserving the existing legacy cognitive-loop contract behind an explicit compatibility adapter.

The intended direction is:

```text
aegis_os.main
→ Kernel
→ canonical CognitiveRuntime
→ canonical pipeline
→ optional simulated execution
```

The temporary compatibility direction is:

```text
legacy caller
→ Kernel.process_goal()
→ explicit legacy compatibility adapter
→ CognitiveRuntime.process_goal()
→ legacy CognitiveOrchestrator
```

The canonical path must become the normal application path. The legacy path must remain available only as an explicit compatibility boundary.

## Authorization Basis

The current repository contains two runtime entry paths:

1. The canonical typed path exposed through `CognitiveRuntime.run()` and `CognitiveRuntime.process()`.
2. The historical path exposed through `CognitiveRuntime.process_goal()` and the legacy `CognitiveOrchestrator`.

`aegis_os.pipeline.composition.create_default_runtime()` already constructs the canonical pipeline and runtime used by the API and benchmark suite.

`Kernel` currently constructs `CognitiveRuntime()` directly without the canonical pipeline and exposes only `process_goal()` as its processing method.

`aegis_os.main` therefore still enters the historical cognitive loop rather than the canonical runtime.

WO-004 authorizes only the bounded convergence required to correct this entry-path split.

## Authoritative Base

Implementation must begin from exactly:

```text
8514de1f4e1bafb73748ec74a9b29e8b2f83d952
Integrate governance records onto main lineage
```

No earlier branch, preserved implementation branch, stash, rejected candidate, or divergent governance lineage is an authorized base.

## Authorized Implementation File List

Only the following implementation, test, and architecture-documentation paths may differ from the authoritative base in a WO-004 candidate.

### Kernel and Runtime

- `aegis_os/core/kernel.py`
- `aegis_os/core/cognitive_runtime.py`
- `aegis_os/core/legacy_compatibility.py` — new file

### Composition and Entry Point

- `aegis_os/pipeline/composition.py`
- `aegis_os/main.py`

### Tests

- `tests/core/test_kernel.py` — new file
- `tests/core/test_cognitive_runtime.py`

### Architecture Documentation

- `docs/architecture/cognitive-pipeline.md`

Any implementation change outside this exact list requires a formal governance amendment before the change is made.

## Governance Record Paths

Documentation & Governance may modify only these governance paths for WO-004 authorization and later disposition records:

- `governance/TRACEABILITY.md`
- `governance/work-orders/WO-004_KERNEL_CANONICAL_RUNTIME_CONVERGENCE.md`

These governance paths are not part of the implementation candidate allowlist.

## Locked Architectural Decisions

1. `Kernel` becomes a canonical-runtime entry boundary.
2. The normal `Kernel` processing path must call the typed canonical runtime.
3. The canonical Kernel method must accept a task, a request identifier, and an explicit execution choice.
4. The canonical Kernel method must return a `CanonicalRuntimeResult`.
5. The canonical pipeline must be configured through the existing composition root rather than duplicated inside `Kernel`.
6. `Kernel.process_goal()` remains temporarily available for backward compatibility.
7. `Kernel.process_goal()` must delegate through an explicit compatibility adapter.
8. The compatibility adapter must contain delegation and lifecycle compatibility only.
9. The compatibility adapter must not implement planning, execution, validation, evaluation, governance, learning, or persistence logic.
10. The legacy `CognitiveOrchestrator` must not become part of the canonical path.
11. The canonical runtime remains the owner of canonical analysis, simulated execution, conformance validation, and result construction.
12. The existing typed runtime contracts and schema version remain unchanged unless a formal amendment explicitly authorizes a change.
13. `aegis_os.main` must use the canonical Kernel path rather than `process_goal()`.
14. The main demonstration must print a serializable canonical result.
15. Only simulated execution is permitted.
16. The API and benchmark composition must not regress.
17. The legacy orchestrator must not be deleted under WO-004.
18. Compatibility preservation does not authorize indefinite duplication; removal of the compatibility path requires a separate work order.

## Required Compatibility Guarantees

- Direct canonical-runtime behavior remains compatible.
- Existing API behavior remains compatible.
- Existing benchmark behavior remains compatible.
- `CognitiveRuntime.process_goal()` remains available during this work order.
- Existing legacy compatibility tests continue to pass.
- `Kernel.process_goal()` remains callable but is visibly separated from the canonical path.
- Existing request-correlation and conformance invariants remain unchanged.
- No real or external execution is introduced.
- No public endpoint is added, removed, or renamed.

## Explicit Non-Goals and Exclusions

WO-004 does not authorize:

- Deletion of `CognitiveOrchestrator`.
- Reimplementation of the cognitive pipeline.
- Changes to intent analysis or agent selection.
- Changes to execution semantics.
- Real execution or external actions.
- Governance execution.
- Evaluation or scoring implementation.
- Learning or memory expansion.
- Persistence changes.
- New API endpoints.
- Dashboard changes.
- Benchmark redesign.
- Schema-version changes.
- Provider or model integration.
- Dependency changes.
- CI or workflow changes.
- Repository cleanup.
- Ruleset or branch-protection changes.
- Tag creation or mutation.
- Modification of `main`.
- Push, merge, release, deployment, or publication.
- Any path outside the exact authorized file lists.

## Acceptance Criteria

A WO-004 implementation candidate is eligible for review only when all of the following are true:

1. The candidate descends from the exact authoritative base.
2. Only authorized implementation paths differ from the base.
3. `Kernel` exposes a canonical typed processing method.
4. The canonical Kernel method delegates to `CognitiveRuntime.run()` or the equivalent typed canonical boundary.
5. The canonical Kernel method returns `CanonicalRuntimeResult`.
6. Default application composition provides a configured canonical pipeline.
7. `aegis_os.main` no longer calls `Kernel.process_goal()`.
8. `aegis_os.main` produces a serializable canonical payload.
9. `Kernel.process_goal()` delegates through the explicit compatibility adapter.
10. The compatibility adapter preserves the established legacy result behavior.
11. The compatibility adapter introduces no independent cognitive or execution logic.
12. Existing canonical-runtime tests pass.
13. New Kernel tests cover canonical routing, request-ID preservation, analysis-only behavior, simulated-execution routing, legacy compatibility routing, lifecycle behavior, and dependency injection.
14. Existing API tests pass.
15. Existing benchmark tests pass.
16. The full repository test suite passes.
17. Ruff lint passes for all authorized Python paths.
18. Ruff formatting validation passes for all authorized Python paths.
19. Repository validation and dependency-integrity checks pass.
20. `git diff --check` passes.
21. The candidate worktree is clean.
22. No unauthorized file, commit ancestry, tag, branch, or remote reference is changed.

## Required Validation Evidence

The Implementation Engineer must provide evidence tied to one exact proposed candidate SHA:

- Candidate SHA and tree.
- Parent SHA.
- Exact changed-path list.
- Base-to-candidate ancestry proof.
- Focused Kernel and canonical-runtime tests.
- Existing API tests.
- Existing benchmark tests.
- Full repository test suite.
- Python 3.11 minimum-version evidence.
- Ruff lint.
- Ruff formatting check.
- Repository validation.
- Dependency integrity.
- Whitespace validation.
- Clean-state verification.
- Confirmation that no remote mutation occurred.
- Confirmation that `main`, tags, rulesets, and unrelated worktrees remained unchanged.

## Review Sequence

1. The Implementation Engineer constructs and validates a bounded implementation branch.
2. Release & Integration may freeze one immutable candidate only under separate candidate-designation authority.
3. QA & Verification evaluates the exact immutable candidate SHA.
4. The Architecture Auditor evaluates the same immutable candidate SHA after QA.
5. Documentation & Governance reconciles scope, evidence, findings, and review verdicts.
6. Any correction requires a new commit and a new candidate designation.
7. Integration into `main` requires a separate explicit authorization.
8. Remote publication requires a separate explicit authorization.

## Stop Conditions

Implementation and review must stop if:

- the base identity differs;
- an unauthorized path changes;
- canonical API or benchmark behavior regresses;
- real execution is introduced;
- the compatibility adapter acquires independent orchestration logic;
- the candidate changes during review;
- required validation cannot be reproduced;
- `main`, a tag, a ruleset, or a remote reference changes without separate authority.

## Current Disposition

```text
WO-004: CLOSED - PUBLISHED TO MAIN
Authoritative base: 8514de1f4e1bafb73748ec74a9b29e8b2f83d952
Implementation scope: COMPLETED
Candidate designated: ce9d17429edc186db74e389e39f5ce6e0677cb35
QA review: PASS
Architecture review: PASS
Integration authority: EXECUTED - COMPLETE
Publication authority: EXECUTED - COMPLETE
Published main: e8de24afa14b564c28ebecd6564e0c111e134924
```
## Candidate review verdict

- Review date: 2026-07-31
- Authorization commit: `1aa7c27248438662272cab22e1b63797845ab6da`
- Candidate commit: `ce9d17429edc186db74e389e39f5ce6e0677cb35`
- Shared authorized base: `8514de1f4e1bafb73748ec74a9b29e8b2f83d952`
- Verdict: **FULL PASS**
- Candidate path count: 5
- Remote mutation during implementation and review: none

### Reviewed candidate paths

1. `aegis_os/core/kernel.py`
2. `aegis_os/core/legacy_compatibility.py`
3. `aegis_os/main.py`
4. `docs/architecture/cognitive-pipeline.md`
5. `tests/core/test_kernel.py`

### Validation evidence

- Identity and commit lineage: PASS
- Authorized implementation boundary: PASS
- Governance evidence and TR-006 linkage: PASS
- Architectural conformance review: PASS
- Full test suite under Python 3.14.6: 179 passed
- Full test suite under Python 3.11.9: 179 passed
- Ruff lint: PASS
- Ruff format: PASS
- Dependency integrity under Python 3.14: PASS
- Dependency integrity under Python 3.11: PASS
- Implementation worktree after review: clean
- Governance worktree before this record: clean
- Temporary Python 3.11 validation environment: removed

### Architectural conclusion

The candidate converges the application Kernel on the shared canonical
`CognitiveRuntime` composition and typed result boundary.

The historical `process_goal()` contract remains available only through the
explicit, lazily initialized `LegacyCompatibilityAdapter`.

The canonical application entry point no longer invokes the historical
orchestrator path. Execution demonstrated by the application remains simulated.

### Governance disposition

The implementation candidate is technically accepted as a valid WO-004
candidate.

This review does not authorize integration, publication, push, modification of
`main`, tagging, release, cleanup, or ruleset changes. A separate explicit
integration authorization is required.
## Post-publication closure

- Closure date: 2026-07-31
- Authoritative base: `8514de1f4e1bafb73748ec74a9b29e8b2f83d952`
- Authorization source: `1aa7c27248438662272cab22e1b63797845ab6da`
- Reviewed candidate: `ce9d17429edc186db74e389e39f5ce6e0677cb35`
- Governance review source: `59ed6530210fc296b50c8d64b7372c08b9db302b`
- Published integration head: `e8de24afa14b564c28ebecd6564e0c111e134924`
- Destination: `refs/heads/main`
- Publication result: **PASS - STRICT FAST-FORWARD**
- Final status: **CLOSED - PUBLISHED TO MAIN**

### Published linear sequence

1. `1b00418c87293f607dfdf76df1aa6325e6610ae7` - Authorize WO-004 kernel runtime convergence
2. `9a39aff6ecd991eade808628d1931ccfd4ac22b3` - Converge Kernel on canonical runtime
3. `e8de24afa14b564c28ebecd6564e0c111e134924` - Record WO-004 candidate review verdict

### Final evidence

- Live remote `main`, `origin/main`, local `main`, and integration HEAD matched the published head.
- Publication used a strict fast-forward.
- No force-push, merge commit, tag, release, or cleanup occurred.
- Integrated repository suite: 179 passed.
- Python 3.11 reviewed-candidate suite: 179 passed.
- Ruff lint, Ruff format, and dependency integrity passed.
- All related worktrees were clean and the original worktree was unchanged.

### Final architectural disposition

The normal application entry path now uses `Kernel.process_task()`, the
configured canonical `CognitiveRuntime`, the canonical request pipeline,
optional simulated execution, conformance validation, and
`CanonicalRuntimeResult`.

The historical `Kernel.process_goal()` path remains available only through the
explicit lazy compatibility adapter. No real execution was introduced.

### Closure boundary

This closure is governance-only. It changes no implementation, test, runtime,
API, benchmark, dependency, CI, ruleset, tag, or release content.

WO-004 is complete. This record grants no further implementation, integration,
publication, cleanup, release, deployment, tag, ruleset, or branch-removal
authority.
