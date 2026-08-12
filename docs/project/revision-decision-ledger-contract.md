# AEGIS Revision / Decision Ledger Contract

## WO-PROJECT-002

WO-PROJECT-002 establishes CMP05 — Revision / Decision Ledger.

The ledger records bounded historical project revisions and decisions.

It does not represent current project state.

## Record Types

The bounded record types are:

- `REVISION`
- `DECISION`

A `REVISION` records that project representation changed.

A `DECISION` records that a bounded project decision was made.

Record type does not imply authority, lifecycle transition, or execution permission.

## Ledger Record

`LedgerRecord` contains exactly seven dimensions:

1. `record_id`
2. `project_ref`
3. `record_type`
4. `summary`
5. `rationale`
6. `affected_state_ref`
7. `sequence`

## Append-only Semantics

Ledger records are immutable after creation.

Records are appended in deterministic sequence order.

Sequence begins at one for each project ledger and increases monotonically.

Existing records are not edited in place.

Existing records are not silently deleted.

WO-PROJECT-002 does not implement database persistence.

The ledger is bounded project history, not persistent cognitive memory.

## Project State Boundary

CMP04 remains the current-state representation.

Appending a `REVISION` does not mutate `ProjectState`.

Appending a `DECISION` does not mutate `ProjectState`.

Ledger history does not automatically become current project state.

Future coordination may use ledger history to inform state changes, but WO-PROJECT-002 does not perform those changes.

## Lifecycle Boundary

WO-PROJECT-002 does not decide whether project-state transitions are valid.

It does not activate, block, complete, cancel, resume, or reopen projects.

PROJECT-003 retains lifecycle ownership.

A ledger record may describe a lifecycle-related decision without performing a lifecycle transition.

## Reasoning Privacy Boundary

`rationale` is bounded explanatory context.

It is not raw chain-of-thought.

It must not be used to store private reasoning traces.

WO-PROJECT-002 does not invoke adaptive reasoning and does not construct `ReasoningRequest`.

## Authority / Execution Boundary

A `DECISION` record is historical representation only.

It does not equal authority approval.

It does not grant execution permission.

It does not invoke tools.

It does not produce a governed verdict.

## Semantic Boundaries

- ledger record != current project state
- ledger record != intent
- ledger record != outcome
- ledger record != plan
- ledger record != reasoning result
- ledger record != lifecycle transition
- ledger record != execution log
- ledger record != approval
- ledger record != authority
- ledger record != governed verdict
- decision record != execution permission
- revision record != state mutation
- no external network
- no persistent cognitive memory
