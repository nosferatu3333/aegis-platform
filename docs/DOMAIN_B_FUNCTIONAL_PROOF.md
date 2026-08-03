# AEGIS MVP Functional Proof - Domain B

Domain B verifies planning and execution boundaries for AEGIS Platform
1.7.0 RC1.

## Scenarios

- `AEGIS-RC1-S05`: bounded plan generation;
- `AEGIS-RC1-S06`: out-of-scope expansion rejection;
- `AEGIS-RC1-S07`: stop-condition cancellation contract.

## S05

S05 uses the canonical `CognitiveRequestPipeline.process_selection` path and
the production `BoundedPlanningAdapter`. It proves that a canonical selection
becomes a finite, non-executing plan with contiguous steps, completion
criteria, evidence requirements, explicit limitations, and canonical IDs.

## S06 boundary

RC1 does not yet contain a semantic classifier for arbitrary scope meaning.
S06 proves the boundary RC1 actually implements: a three-step plan is
accepted, a fourth injected step expands the workflow, the production
`PlanningBounds(max_steps=3)` contract rejects it, and no expanded plan or
execution is emitted.

## S07 boundary

RC1 contains a canonical `CANCELLED` execution state and conformance rules
requiring a completed prefix, skipped suffix, zero failed steps, terminal
timestamps, and no false completed result.

RC1 does not yet expose a live runtime stop-request hook. S07 therefore uses
a controlled fixture to activate a recorded stop condition and validates the
result through production execution and conformance contracts.

## Run all Domain B scenarios

```powershell
python -m aegis_os.proof.domain_b
```

## Run one scenario

```powershell
python -m aegis_os.proof.domain_b --scenario AEGIS-RC1-S07
```

Generated evidence is written under
`artifacts/functional-proof/domain-b/`, is ignored by Git, and is not a signed
release artifact.
