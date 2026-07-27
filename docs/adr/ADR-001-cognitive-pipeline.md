# ADR-001 — Deterministic cognitive pipeline

- **Status:** Accepted
- **Date:** 2026-07-26

## Context

The legacy repository contained multiple cognitive, planning, memory, and
learning prototypes without one product-facing request/result path. The
v0.1.0 milestone needed inspectable behavior, stable serialization, and tests
before adaptive reasoning was introduced.

## Decision

Use a synchronous deterministic pipeline as the initial operational spine:
mission normalization, keyword intent analysis, required-capability mapping,
exact profile selection, workflow generation, and `CognitiveRequestResult`.
Keep composition explicit and reuse it from API and benchmarks.

## Consequences

- Results are repeatable, explainable, serializable, and easy to test.
- No-match behavior can be explicit rather than falling through to an agent.
- Later execution and benchmark layers consume the same contracts.
- Capability remains limited by keyword vocabulary and exact matching.

## Alternatives considered

- LLM-first classification: deferred because it introduces nondeterminism,
  dependencies, evaluation ambiguity, and network/model concerns.
- Reuse the legacy orchestrator as the API result: rejected for the MVP because
  its custom objects, side effects, and separate simulation did not match the
  stable request/response contract.
- Put analysis logic in API handlers: rejected to keep the lifecycle reusable.

## Current limitations

No semantic understanding, adaptive policy, learned confidence, execution
profile in the default registry, or integration with legacy memory/learning.

## Related modules and releases

`aegis_os.pipeline.*`, `aegis_os.agents.capability_matcher`,
[cognitive pipeline](../architecture/cognitive-pipeline.md),
[v0.1.0](../releases/v0.1.0.md), and
[v0.4.0](../releases/v0.4.0.md).
