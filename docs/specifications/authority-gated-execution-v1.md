# Authority-Gated Execution Adapter v1

WO-MVP-007 introduces the Platform boundary that converts a canonical
`BoundedPlan` into an `ExecutionRequest` only after every plan step has been
explicitly evaluated against canonical Core authority records.

## Boundary

```text
BoundedPlan
→ per-step authority evaluation
→ allow | pause | deny
→ ExecutionRequest only when every step is allowed
```

The adapter never creates grants, infers approval, expands scope, or executes a
partially authorized plan.

## Rules

- `none` allows the declared step without an additional grant.
- `approval_required` requires one active, unexpired grant covering the plan,
  actor, full requested scope, and consequence class.
- `prohibited` denies execution.
- `unknown` pauses execution.
- Explicit denials override otherwise valid grants.
- Confirmed revocation blocks any overlapping grant scope.
- Missing, expired, under-scoped, under-ranked, or wrong-grantee grants pause.
- Every decision emits an attributable `AuthorityAuditEvent`.
- An execution request is created only when all decisions are `allow`.

The scope vocabulary is deterministic:

- `execute:plan:<plan_id>`
- `execute:step:<step_id>`
