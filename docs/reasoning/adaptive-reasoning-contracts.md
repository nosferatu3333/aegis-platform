# AEGIS Adaptive Reasoning Contracts

## WO-REASON-001 scope

This work order establishes the first implementation contract for adaptive
reasoning.

It does not implement the full adaptive reasoning system.

## Reasoning modes

The canonical modes are:

- `DIRECT`
- `VERIFY`
- `BRANCH`
- `SEARCH`

A later work order will define the escalation policy that selects among them.

## `ReasoningRequest`

`ReasoningRequest` bounds the cognitive problem presented to the reasoning
controller.

It includes:

- request identity;
- intent reference;
- outcome reference;
- project-context reference;
- uncertainty signals;
- risk signals;
- constraints;
- requested depth;
- bounded cognitive budget.

It deliberately contains no authority grant or execution permission.

## `ReasoningResult`

`ReasoningResult` is a bounded reasoning-control result.

It can expose:

- selected reasoning mode;
- safe summary;
- selection rationale;
- uncertainty;
- evidence requirements;
- preserved alternatives;
- whether the current reasoning cycle is complete.

It is not:

- an approval;
- an authority grant;
- an execution request;
- an execution receipt;
- a tool invocation.

## Semantic boundary

Reasoning quality does not create authority.

A stronger recommendation does not create permission.

A completed reasoning cycle does not imply execution.

## Deferred implementation

The following remain outside WO-REASON-001-C2:

- escalation policy;
- candidate generation;
- candidate evaluation;
- convergence control;
- project persistence;
- persistent cognitive memory;
- tool execution;
- real-world authority expansion;
- API integration;
- user-interface redesign.

## Serialization

Both request and result expose deterministic `to_dict()` representations with
`schema_version = "1.0"`.

The serialization is suitable for future API, test, audit, evidence, and safe
projection integration without exposing raw internal reasoning.
## Reasoning controller interface

WO-REASON-001-C3 adds the `ReasoningController` boundary.

The controller accepts:

`ReasoningRequest`

and returns:

`ReasoningResult`

The interface establishes the point where future adaptive reasoning policy will
operate.

### Static contract controller

`StaticReasoningController` exists only to prove the controller contract.

Its reasoning mode is supplied explicitly.

It does not inspect uncertainty, risk, complexity, consequence, evidence
conflict, reversibility, or cross-domain requirements to choose a mode.

That behavior belongs to WO-REASON-002.

### Controller boundary

A reasoning controller may:

- inspect a bounded reasoning request;
- coordinate cognitive processing;
- select or report a reasoning mode;
- return a bounded reasoning result.

A reasoning controller may not:

- grant authority;
- infer permission;
- execute tools;
- produce external side effects;
- mutate persistent cognitive memory;
- bypass downstream governance.

Therefore:

REASONING CONTROLLER
!=
AUTHORITY CONTROLLER

and:

REASONING RESULT
!=
EXECUTION PERMISSION
