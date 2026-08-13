# Bounded cognitive-cycle contract

## SYSTEM ownership

`aegis_os.system` owns typed SYSTEM request and result contracts, explicit
project-context routing, and one synchronous composition through existing
CMP01, CMP03, CMP04, and CMP07–CMP11 interfaces. It does not redefine the
semantics owned by those components.

The package exports exactly `CognitiveCycle`, `CognitiveCycleRequest`,
`CognitiveCycleResult`, `CycleDisposition`, `NextInteraction`,
`ProjectContext`, `ProjectContextMode`, and `ReasoningHandoffResult`.

## Request contract

`CognitiveCycleRequest` is immutable and contains explicit correlation IDs, an
existing `IntentRequest`, explicit `ProjectContext`, success conditions,
outcome uncertainties, risk signals, requested reasoning depth, and budget.
Caller constraints remain inside `IntentRequest.explicit_constraints`.
There is no caller-supplied inferred-constraint field or permission, authority,
tool, execution, persistence, memory, or project-change payload.

## Project context

The exact context modes are:

- `TRANSIENT`: no project identifier or state; creates and persists nothing.
- `CREATE_NEW`: requires a non-empty project ID and delegates exactly once to
  `ProjectStateManager.create()` after outcome construction.
- `EXISTING`: requires an explicit authoritative `ProjectState`, performs no
  lookup, and returns that exact immutable object without replacement.

Contradictory and missing context combinations are rejected deterministically.
The SYSTEM layer never invokes a project lifecycle transition or ledger append.

## Clarification gate and constraint provenance

Each cycle calls `IntentInterpreter.interpret()` exactly once and consumes only
the public `clarification_required` and `clarification_questions` fields. When
clarification is required, the cycle returns `CLARIFICATION_REQUIRED` with
`USER_CLARIFICATION`; outcome modeling, project routing, and reasoning are not
called. CMP02 is not invoked a second time.

For eligible requests, caller constraints originate from
`IntentRequest.explicit_constraints`, while inferred constraints originate
only from `IntentInterpretation.inferred_constraints`. CMP03 remains the
`OutcomeModel` owner. Reasoning constraints preserve stable order across
explicit outcome constraints, inferred outcome constraints, and additional
project constraints while removing duplicates.

## One bounded synchronous flow

```text
CognitiveCycleRequest
  -> CMP01 IntentInterpreter (once)
  -> public clarification gate
  -> CMP03 OutcomeModeler (once when eligible)
  -> TRANSIENT / CREATE_NEW / EXISTING routing
  -> one bounded ReasoningRequest
  -> CMP07-CMP11 AdaptiveReasoningCycle (once)
  -> ReasoningHandoffResult
  -> CognitiveCycleResult
```

There is no retry, recursion, background task, scheduler, autonomous loop, or
hidden second pass. `DIRECT`, `VERIFY`, `BRANCH`, and `SEARCH` retain their
existing reasoning meanings. BRANCH performs its existing bounded
generate/evaluate/converge pass once.

## Reasoning handoff and result semantics

`ReasoningHandoffResult` correlates the public bounded `AdaptiveCycleResult`
with the reasoning request ID. It contains no raw chain-of-thought, scratchpad,
token trace, private scoring trace, or hidden deliberation.

`CognitiveCycleResult` is immutable and distinguishes clarification, transient
or project reasoning, tied or insufficient branch convergence, verification
signals, and search signals. VERIFY coordinates later evidence interaction but
performs no retrieval or governed validation. SEARCH coordinates later search
interaction but performs no network, connector, retrieval, or tool action.
Reasoning convergence is non-authoritative.

The result contains no proposal, approval, authority, governed verdict,
execution permission, execution result, tool command, lifecycle command,
ledger record, persistent memory, or project-state mutation.

## Immutability and determinism

Requests, project contexts, handoff results, and cycle results are frozen,
slotted dataclasses. Structural validation is eager and deterministic.
Equivalent deterministic collaborators and inputs produce equivalent public
result serialization. TRANSIENT creates no project identity, CREATE_NEW
preserves the exact CMP04-created state, and EXISTING preserves the exact
caller-supplied state identity.

## Explicit non-goals

SYSTEM-002 adds no authority, validation, execution, network, tools,
filesystem mutation, persistence, cognitive memory, workflow engine, service
registry, event bus, plugin system, or project-change policy.
`ProjectChangeProposal` and related mutation recommendations remain deferred
and out of scope.
