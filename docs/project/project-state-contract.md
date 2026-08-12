# AEGIS Project State Contract

## WO-PROJECT-001

WO-PROJECT-001 establishes CMP04 — Project State Manager.

A project state is the current operational representation of an objective in progress.

## Project State Model

`ProjectState` contains exactly six dimensions:

1. `project_id`
2. `outcome_ref`
3. `status`
4. `current_state`
5. `active_constraints`
6. `unresolved_issues`

## Status Model

The bounded status vocabulary is:

- `NOT_STARTED`
- `ACTIVE`
- `BLOCKED`
- `COMPLETED`
- `CANCELLED`

Status represents project-state classification only.

Status does not grant authority, approval, or execution permission.

## Outcome Boundary

CMP04 consumes or references an established `OutcomeModel`.

Project state does not:

- reinterpret intent;
- redefine outcome semantics;
- mutate the outcome;
- manufacture success conditions;
- silently modify explicit constraints;
- silently promote inferred constraints to explicit constraints.

## Constraint Handling

By default, active constraints are derived from the outcome's explicit and inferred constraint collections.

The project-state representation does not change the provenance stored in the governing outcome.

An explicit `active_constraints` tuple may be supplied when the caller needs to represent the currently applicable subset.

## Current State

`current_state` describes where the project presently stands.

It does not prescribe implementation steps.

It is not a plan.

## Unresolved Issues

`unresolved_issues` preserves unresolved project-state conditions.

Recording an unresolved issue does not automatically change project status.

## Lifecycle Boundary

PROJECT-001 models state only.

It does not implement lifecycle transition policy.

PROJECT-003 owns lifecycle semantics.

A status value may be represented without determining whether a transition to that status is permitted.

PROJECT-001 does not automatically transition status.

PROJECT-001 does not infer completion from activity.

`COMPLETED` reports project state only; it does not itself validate outcome satisfaction.

## Ledger Boundary

PROJECT-001 does not own revision history.

PROJECT-001 does not own decision history.

PROJECT-001 does not record immutable project events.

PROJECT-002 owns Revision / Decision Ledger semantics.

## Reasoning Boundary

PROJECT-001 does not:

- construct `ReasoningRequest`;
- select DIRECT / VERIFY / BRANCH / SEARCH;
- generate candidates;
- evaluate candidates;
- converge candidates;
- invoke adaptive reasoning.

Project-to-reasoning mapping belongs to later system integration.

## Semantic Boundaries

- project state != intent
- project state != outcome
- project state != plan
- project state != reasoning result
- project state != candidate path
- project state != decision ledger
- project state != lifecycle engine
- project state != execution state
- project state != execution authority
- project state != governed verdict
- status != authority
- status != approval
- status != execution permission
- no tool invocation
- no external network
- no persistent cognitive memory
