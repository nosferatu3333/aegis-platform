# Bounded Planning Adapter v1

WO-MVP-006 establishes the canonical boundary between capability selection and
Platform planning.

## Contract flow

```text
Core CapabilitySelection
→ Platform workflow normalization
→ authority and consequence preservation
→ Core BoundedPlan
```

The adapter creates planning output only. It does not execute a step, grant
approval, infer authority, or claim that completion evidence exists.

## Invariants

- Every plan is linked to one request, interpretation, and selection.
- Step sequence is ordered, unique, and bounded by configuration.
- Every step declares completion criteria and the authority required to run it.
- Moderate, high, and critical plans declare stop conditions.
- Expected evidence is explicit before execution begins.
- The serialized result states that no step has been executed.
- A canonical capability selection may enter Platform without re-running the
  legacy local selector.

## Platform ownership

Platform owns workflow normalization and bounded orchestration. Canonical
selection and planning schemas remain owned by `aegis-core`. Capability
eligibility and selection remain owned by `aegis-ops`.
