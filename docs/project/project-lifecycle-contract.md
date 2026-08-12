# Project lifecycle contract

## Scope

`ProjectLifecycleManager` owns only deterministic structural transitions between
existing `ProjectStatus` values. It does not interpret intent, reason about a
project, authorize actions, execute work, validate outcomes, persist memory, or
record history.

## Public contract

```python
LifecycleTransitionResult(
    source_status: ProjectStatus,
    target_status: ProjectStatus,
    permitted: bool,
    resulting_state: ProjectState | None,
)

ProjectLifecycleManager().transition(
    project_state,
    target_status,
    current_state="Caller-supplied project state.",
)
```

`current_state` is mandatory, keyword-only, and supplied by the caller. The
lifecycle manager never fabricates transition narrative.

## Frozen transition graph

| Source | Permitted targets |
|---|---|
| `NOT_STARTED` | `ACTIVE`, `CANCELLED` |
| `ACTIVE` | `BLOCKED`, `COMPLETED`, `CANCELLED` |
| `BLOCKED` | `ACTIVE`, `CANCELLED` |
| `COMPLETED` | none |
| `CANCELLED` | none |

Every other edge is rejected, including every self-transition. `COMPLETED` and
`CANCELLED` are terminal.

A rejected, well-typed edge is represented by `permitted=False` and
`resulting_state=None`. Invalid input types or missing required lifecycle input
are contract errors rather than transition decisions.

## Immutability and preservation

A permitted transition returns a new immutable `ProjectState`. It leaves the
source state unchanged and preserves exactly:

- `project_id`
- `outcome_ref`
- `active_constraints`
- `unresolved_issues`

Only `status` and the explicit caller-supplied `current_state` change.

`LifecycleTransitionResult` is immutable and serializes exactly
`source_status`, `target_status`, `permitted`, and `resulting_state`, in that
order.

## Completion boundary

`ProjectStatus.COMPLETED` means only that the lifecycle representation is
complete. It does not assert objective satisfaction, successful validation,
approval, authority, execution permission, governed verdict, execution result,
or real-world completion.

## Ledger and subsystem boundaries

Lifecycle transition and revision/decision history are separate. The lifecycle
manager does not accept or mutate `ProjectLedger` and does not append records.
A later caller may choose to record a transition explicitly.

The lifecycle module imports only the existing project models and standard
library dataclass support. It does not import or invoke intent, reasoning,
authority, validation, execution, tools, networking, resources, memory, or
persistence. It stores no reasoning trace or chain-of-thought.
