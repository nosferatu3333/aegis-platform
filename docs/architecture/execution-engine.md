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
```

## Contracts

`aegis_os.execution.models` defines schema version `1.0` contracts:

- `ExecutionRequest`: request ID, mission, selected agent, capabilities,
  workflow steps, constraints, permissions, and metadata.
- `ExecutionStep`: stable step ID, order, description, status, inputs, outputs,
  and optional error.
- `ExecutionReceipt`: request identity, mission, agent, final status, all
  steps, timestamps, counts, audit logs, `simulated`, and schema version.

Request statuses are `pending`, `ready`, `running`, `waiting`, `completed`,
`failed`, and `cancelled`. Step statuses are `pending`, `running`, `completed`,
`failed`, and `skipped`.

## Adapter and eligibility

`build_execution_request()` accepts only a `PipelineStatus.READY`
`CognitiveRequestResult`. It preserves the mission, selected agent, required
capabilities, and workflow order. Failed/no-match analyses are rejected before
execution.

The `constraints` and `permissions` fields are descriptive inputs in v0.3.0;
there is no policy engine that enforces their contents.

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
workflow, descriptions, or valid unique positive orders.

## Controlled failure

The reserved marker `[simulate-failure]` in a step description is the only
controlled failure mechanism. The current step becomes `failed`, later steps
become `skipped`, the receipt becomes `failed`, counts are updated, and the
failure is recorded in audit logs. Ordinary mission text does not randomly
fail.

## Receipt and audit evidence

Receipts contain start/finish timestamps, final request status, ordered step
states, deterministic outputs or errors, completed/failed counts, lifecycle log
entries, and `simulated: true`. Standard Python logging records request
creation, request and step transitions, agent identity, completion/failure, and
the simulation flag. Receipts are returned but not persisted.

## API integration

`POST /execute-task` validates the same task body as `/analyze-task`, runs the
existing cognitive pipeline, adapts a ready result, executes the simulation,
and returns:

```json
{
  "analysis": {},
  "execution": {},
  "simulated": true
}
```

The dashboard exposes a separate **Simulate Execution** control and explicit
simulation warning. `/analyze-task` remains analysis-only.

## Limitations

- No real tool adapter, policy decision, approval, isolation, or authorization.
- No retries, queues, workers, cancellation API, or waiting transition.
- Single-agent, synchronous, in-memory operation.
- No durable receipt or audit store.
- Outputs do not establish mission quality or external completion.

See [ADR-002](../adr/ADR-002-governed-execution.md),
[governance](governance.md), and the
[v0.3.0 release](../releases/v0.3.0.md).
