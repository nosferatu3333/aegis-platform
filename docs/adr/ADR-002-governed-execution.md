# ADR-002 — Governed simulation before external execution

- **Status:** Accepted
- **Date:** 2026-07-26

## Context

v0.2.0 generated visible workflows but had no execution semantics. Adding real
tools at that point would have preceded stable lifecycle states, failure
behavior, permissions, audit evidence, and policy boundaries.

## Decision

Introduce explicit execution request, step, and receipt contracts and a
deterministic simulated engine first. Restrict it to ready pipeline results,
ordered transitions, a single reserved test-failure marker, audit logs, and
`simulated: true`. Perform no external action.

## Consequences

- State and failure contracts can mature independently from tool adapters.
- API and dashboard users can distinguish analysis from simulated execution.
- Receipts provide inspectable request-local evidence.
- “Governed” currently means bounded lifecycle behavior, not a complete policy
  engine.

## Alternatives considered

- Directly execute workflow descriptions: rejected as arbitrary and unsafe.
- Embed execution inside the analysis pipeline: rejected because it would
  couple proposed work to side effects and change `/analyze-task`.
- Return only a final status: rejected because step transitions and failures
  would not be auditable.

## Current limitations

No enforced permissions, approvals, isolation, real adapters, durable audit
store, retries, queues, waiting/cancellation API, or multi-agent execution.

## Related modules and releases

`aegis_os.execution.*`, `aegis_os.api.app`,
[execution architecture](../architecture/execution-engine.md),
[governance status](../architecture/governance.md), and
[v0.3.0](../releases/v0.3.0.md).
