# ADR-006 — Provider-neutral Environment Interaction Layer

- **Status:** Accepted

## Context

The implemented Operational Resource Foundation can resolve semantic resource
requirements to stable references, while current execution remains simulated
and has no external interaction boundary. The earlier ADR-004 established the
direction of a governed adapter boundary before resource contracts existed.
Phase B now needs a precise resource-to-environment handoff without coupling
cognition to providers.

## Decision

Introduce a provider-neutral Environment Interaction Layer between resolved
operational resources and external or simulated environments.

The layer uses semantic operations, immutable explicit requests, normalized
results, deterministic environment resolution, separate policy and approval
boundaries, adapter isolation, and immutable interaction receipts. Phase B
begins with deterministic simulation and no external I/O.

This ADR supersedes ADR-004 as the current decision record while preserving it
as historical context.

## Decision drivers

- provider-neutral cognition and capability selection;
- explicit resource handoff and side effects;
- default-deny governance and independent approval;
- deterministic, auditable environment selection;
- provider failure containment and normalized evidence;
- compatibility with Phase A and current execution.

## Scope

In scope for design are requests, results, operations, environment/adapter
definitions, explicit registry and resolution, policy/approval interfaces,
simulation adapters, and receipts. Runtime implementation, live providers,
credentials, persistence, execution integration, observations, memory, and
reflection are outside this architecture task.

## Consequences

- Cognition and execution do not invoke provider APIs directly.
- Resource resolution remains separate from environment resolution.
- Every interaction crosses validation, environment resolution, policy,
  approval, adapter, normalization, and receipt boundaries.
- Adapters declare support but cannot grant authorization.
- Simulation and live execution cannot be silently interchanged.
- Additional contracts and evidence increase implementation discipline and
  complexity.

## Alternatives considered

Direct tool invocation, provider-specific planning, adapter-only abstraction,
an untyped universal executor, environment data in resource references,
adapter-owned policy, merged results/receipts, immediate live I/O, automatic
discovery, and adaptive ranking were rejected because they weaken semantic
clarity, governance, isolation, or determinism.

## Security implications

The design requires default deny, least privilege, explicit side effects,
secret-free bounded contracts, output sanitization, untrusted-content
classification, adapter isolation, approval separation, immutable minimized
receipts, replay/idempotency controls, and strict prevention of simulation-to-
live escalation.

## Compatibility implications

Phase A resource contracts remain authoritative and unchanged. Existing
pipeline, execution, API, dashboard, and benchmark behavior remains unchanged
until later explicitly specified integration. Versioned contracts and receipts
allow future adapters without provider changes to cognition.

## Acceptance conditions

Accept only after architecture review confirms operation semantics, ownership,
resource handoff, lifecycle ordering, deterministic resolution, policy and
approval separation, failure taxonomy, security, receipt boundaries, and the
simulation-first runtime scope.

## Deferred decisions

Exact operation enums, environment identity, adapter and policy protocols,
approval tokens, result payload typing, timeout/idempotency/partial-result
representations, receipt persistence and integration shape, schema versions,
and detailed reason codes belong in the Phase B implementation specification.

## Related documents

- [Environment Interaction Layer](../architecture/environment-interaction-layer.md)
- [Operational Resource Model](../architecture/operational-resource-model.md)
- [ADR-004 historical precursor](ADR-004-environment-interface.md)
- [ADR-005](ADR-005-operational-resource-model.md)
## WO-005 acceptance record

- Acceptance date: 2026-07-31
- Governing work order: `WO-005`
- Architectural base: `be7502f73b51808d54728f912ead46ad0073c7b9`
- Governance amendment main: `ad743b4568bbd82527f7ff192c5b10ca4d59c2e9`
- Accepted scope: provider-neutral, deterministic, simulation-only Phase B design
- Runtime implementation: not included
- Live providers, credentials, persistence, and external I/O: not authorized

Architecture, specification, and roadmap reconciliation confirm that Phase B
remains isolated from the current cognitive pipeline, execution engine, API,
dashboard, and benchmark fixtures.

The accepted implementation contract is the existing
[`v0.5 Phase B — Environment Interaction Layer implementation specification`](../specifications/v0.5-phase-b-environment-interaction-layer.md).

Acceptance of this ADR does not authorize implementation, integration,
publication of this candidate, live execution, provider access, tagging,
release creation, ruleset modification, or cleanup.
