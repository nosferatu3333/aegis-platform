# Governance status

AEGIS does not currently contain a full governance engine.
`aegis_os.governance` is an empty package. The controls below are operational
boundaries around deterministic simulation, not policy enforcement.

## Implemented

- API validation rejects blank or structurally invalid task requests.
- Request IDs correlate API responses and standard-library log entries.
- Pipeline outcomes distinguish `ready` from explicit no-match `failed`.
- Only ready analyses can be adapted into execution requests.
- Execution validates identity, agent, workflow presence, descriptions, and
  unique positive step order.
- Request and step transitions are deterministic and recorded in receipts.
- Controlled failure stops work and marks subsequent steps `skipped`.
- Receipts always serialize `simulated: true`.
- Benchmarks validate agent selection, statuses, workflow order, and simulation
  compliance against external deterministic cases.

## Partial

- Intent analysis calculates `RiskLevel`, but risk does not affect execution.
- `ExecutionRequest` carries `constraints` and `permissions`, but the engine
  does not interpret or enforce them.
- Logs and receipts provide request-local audit evidence, but there is no
  durable, tamper-evident audit store.
- Failure semantics cover malformed requests and one reserved simulation
  marker, not tool, timeout, policy, or recovery failures.
- API request correlation exists, but authentication, user identity, tenancy,
  and authorization do not.

## Planned

Future governance requires explicit policy decisions before any real action:

- resource visibility, resolution, ownership, classification, and retention
  decisions;
- typed tool capabilities and least-privilege grants;
- allow, deny, and human-approval decisions;
- risk-to-policy mapping with bypass prevention;
- isolated adapters, secrets boundaries, and resource scopes;
- cancellation, time/budget limits, idempotency, and failure recovery;
- durable, attributable, integrity-protected audit events;
- policy versioning and benchmark cases for approval/denial matrices.

These items are proposals in the [roadmap](../roadmap/ROADMAP.md), not current
capabilities. See [ADR-002](../adr/ADR-002-governed-execution.md) and the
[execution engine](execution-engine.md). The proposed common external boundary
is documented in the
[Environment Interaction Layer](environment-interface.md) and
[ADR-004](../adr/ADR-004-environment-interface.md). The semantic target,
resolution, ownership, and provenance boundary is proposed in the
[Operational Resource Model](operational-resource-model.md) and
[ADR-005](../adr/ADR-005-operational-resource-model.md).
