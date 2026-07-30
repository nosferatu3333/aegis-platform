# Governed simulated execution engine

## Scope and boundary

The execution layer deterministically simulates workflow transitions and
produces an auditable receipt. It does **not** invoke external tools, access the
internet, call external APIs, run shell commands, or mutate user resources.

```text
CognitiveRequestResult
  -> build_execution_request
  -> ExecutionRequest
  -> ExecutionEngine
  -> ExecutionReceipt
  -> ExecutionConformanceValidator
```

## Contracts

`aegis_os.execution.models` defines schema version `1.0` contracts:

- `ExecutionRequest`: request ID, mission, selected agent, typed execution
  mode, capabilities, workflow steps, constraints, permissions, and metadata.
- `ExecutionStep`: stable step ID, order, description, status, inputs, outputs,
  and optional error.
- `ExecutionReceipt`: request identity, mission, agent, typed execution mode,
  final status, all steps, timestamps, counts, audit logs, the compatibility
  `simulated` flag, and schema version.
- `ExecutionConformanceResult`: request correlation, terminal operation
  outcome, aggregate conformance status, all required checks, evidence, and
  conformance schema version.

Request statuses are `pending`, `ready`, `running`, `waiting`, `completed`,
`failed`, and `cancelled`. Step statuses are `pending`, `running`, `completed`,
`failed`, and `skipped`.

`ExecutionMode.SIMULATED` is the only supported execution mode. It is the
machine-readable simulation boundary. Descriptive constraints and permission
labels do not establish execution mode.

## Adapter and eligibility

`build_execution_request()` accepts only a `PipelineStatus.READY`
`CognitiveRequestResult`. It preserves the mission, selected agent, required
capabilities, and workflow order. Failed/no-match analyses are rejected before
execution.

The `constraints` and `permissions` fields remain descriptive inputs; there is
no policy engine that enforces their contents.

## Deterministic lifecycle

Successful requests follow:

```text
pending -> ready -> running -> completed
```

Each step is sorted by workflow order and follows:

```text
pending -> running -> completed
```

The output is a deterministic message identifying the simulated step. The
engine does not sleep. A clock can be injected for repeatable tests and
benchmarks.

Malformed requests are rejected for missing identity, mission, selected agent,
typed simulated execution mode, workflow, descriptions, or valid unique
positive orders.

## Controlled failure

The reserved marker `[simulate-failure]` in a step description is the only
controlled failure mechanism. The current step becomes `failed`, later steps
become `skipped`, the receipt becomes `failed`, counts are updated, and the
failure is recorded in audit logs. Ordinary mission text does not randomly
fail.

## Cancellation invariants

There is no cancellation API or engine cancellation transition. A
`CANCELLED` receipt can nevertheless be validated as an imported terminal
receipt when all of these invariants hold:

- the receipt has ordered workflow steps and both start and finish timestamps;
- the finish timestamp is not earlier than the start timestamp;
- zero or more leading steps are `completed`;
- every remaining step is `skipped`;
- at least one step is skipped, so an all-completed receipt is not cancelled;
- `completed_steps` matches the completed prefix and `failed_steps` is zero;
- no `pending`, `running`, or `failed` step appears.

A failed step belongs only to a `FAILED` receipt. A failed receipt has exactly
one failed step, completed steps before it, and skipped steps after it.

## Execution conformance

`ExecutionConformanceValidator` runs once after simulated execution. It checks
request identity, mission and capability preservation, planned workflow,
ordering, completeness, terminal state, and the typed simulation boundary.
It performs no quality assessment, evaluation, governance decision, or
authorization.

Conformance status and operation outcome are independent. A controlled
execution failure can therefore return operation outcome `failed` with
conformance status `passed`.

### Normal conformance failure

Failed conformance remains a valid canonical result with runtime status
`conformance_failed`; it is not raised as an exception. The result retains the
analysis, execution receipt, individual checks, evidence, operation outcome,
and correlated request identity. The execution receipt outcome remains
independent from the conformance outcome. The API returns this complete
canonical evidence as a structured HTTP 500 response.

### Runtime invariant failure

A runtime invariant failure means the server produced or encountered an
impossible canonical or validator contract state. In this case, an ordinary
canonical conformance result cannot be trusted or constructed. The runtime
uses the dedicated `CanonicalRuntimeInvariantError` classification, and the
API returns HTTP 500 with a stable error code and safe description.

This classification is not a client-input or readiness failure, ordinary
execution failure, or normal failed-conformance result. It carries no
`conformance_failed` payload because no valid canonical result exists.

## Receipt and audit evidence

Receipts contain start/finish timestamps, final request status, ordered step
states, deterministic outputs or errors, completed/failed counts, lifecycle
log entries, `execution_mode: simulated`, and `simulated: true`. Standard
Python logging records request creation, request and step transitions, agent
identity, completion/failure, and the simulation flag. Receipts are returned
but not persisted.

## API integration

`POST /execute-task` validates the same task body as `/analyze-task`, runs the
existing cognitive pipeline, adapts a ready result, executes the simulation,
validates conformance, and returns:

```json
{
  "analysis": {},
  "execution": {
    "schema_version": "1.0",
    "execution_mode": "simulated",
    "simulated": true
  },
  "validation": {
    "schema_version": "1.0",
    "status": "passed",
    "operation_outcome": "completed",
    "checks": [],
    "evidence": []
  },
  "simulated": true
}
```

The dashboard exposes separate simulated-execution and validation stages.
`/analyze-task` remains analysis-only.

API failure classification is:

| Condition | HTTP status | Contract |
|---|---:|---|
| Invalid request body or blank task | 422 | Request-validation detail |
| Analysis not ready for execution | 422 | Existing analysis-rejection detail |
| Faithfully represented execution failure | 200 | Execution `failed`, conformance `passed` |
| Failed execution conformance | 500 | Structured canonical result with `conformance_failed`, receipt, and validation evidence |
| Internal canonical runtime invariant failure | 500 | Stable internal error code and safe description; no canonical conformance payload |

The HTTP 500 mapping identifies a server-side conformance failure without
discarding the canonical result. It does not reinterpret the failure as invalid
client input. A separate HTTP 500 contract classifies impossible internal
runtime states without presenting them as valid conformance results or exposing
internal details. Execution remains synchronous, in-memory, and simulated; no
external execution is introduced.

## API compatibility decision

The `validation` response member and `execution.execution_mode` member are
classified as backward-compatible additive fields under existing schema
version `1.0`. Existing response members retain their names and meanings,
`/analyze-task` is unchanged, both additions have deterministic defaults or
successful-response values, and repository contract policy requires readers
to preserve or ignore safe unknown fields.

Consumers that reject unknown JSON members are stricter than this
compatibility policy and must update their decoders. Removing or renaming an
existing field, changing its meaning, or changing an existing value type would
require a new schema version and migration rules.

## Limitations

- No real tool adapter, policy decision, approval, isolation, or authorization.
- No retries, queues, workers, cancellation API, or waiting transition.
- Single-agent, synchronous, in-memory operation.
- No durable receipt or audit store.
- Outputs and conformance do not establish mission quality or external
  completion.

See [ADR-002](../adr/ADR-002-governed-execution.md),
[governance](governance.md), and the
[v0.3.0 release](../releases/v0.3.0.md).
