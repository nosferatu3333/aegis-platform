# AEGIS Intent Interpretation Contract

## WO-INTENT-001

WO-INTENT-001 establishes two distinct components:

- CMP01 — Intent Interpreter
- CMP02 — Clarification Engine

The intent layer exists before adaptive reasoning.

Its purpose is to determine what the user is trying to accomplish and whether
the request is sufficiently understood to proceed.

## Primary primitive

The primary primitive is **INTENT**.

Intent is not equivalent to the literal prompt.

Intent is not a plan.

Intent is not an outcome.

Intent is not authority.

Intent is not execution permission.

## Input contract

`IntentRequest` contains:

- `raw_request`
- `context_refs`
- `explicit_constraints`

Context references identify already-available targets or artifacts.

Explicit constraints are preserved exactly and are never silently converted
into inferred constraints.

## Intent interpretation

`IntentInterpretation` contains exactly eight dimensions:

1. `raw_request`
2. `interpreted_intent`
3. `intent_type`
4. `explicit_constraints`
5. `inferred_constraints`
6. `ambiguities`
7. `clarification_required`
8. `clarification_questions`

The initial implementation deliberately uses conservative deterministic rules.

It does not claim semantic omniscience.

## Intent types

The bounded initial taxonomy is:

- `UNDERSTAND`
- `DECIDE`
- `CREATE`
- `CHANGE`
- `EVALUATE`
- `PLAN`
- `EXECUTE_REQUEST`

`EXECUTE_REQUEST` describes the orientation of the request.

`EXECUTE_REQUEST` does not grant execution authority.

## Explicit versus inferred information

User-stated constraints remain explicit.

Inferred constraints remain separately identifiable.

The minimum implementation does not fabricate inferred constraints merely to
populate the field.

Inference != explicit user statement.

## Ambiguity

`IntentAmbiguity` records:

- a machine-readable code;
- a bounded description;
- whether the ambiguity is blocking;
- a clarification question when blocking.

Blocking ambiguity means the unresolved interpretation could materially change
the target, operation, outcome, constraints, scope, or downstream reasoning.

## Clarification Engine

`ClarificationEngine` consumes recorded ambiguities.

It returns:

- `SUFFICIENT`; or
- `CLARIFICATION_REQUIRED`.

Only blocking ambiguities produce clarification questions.

Non-blocking ambiguity may remain recorded while processing continues.

Mere incompleteness is not automatically blocking.

Clarification must not become habitual interrogation.

## Initial blocking cases

The minimum implementation recognizes bounded cases including:

- unresolved placeholders;
- unresolved target references for target-sensitive operations when no context
  reference is available.

These are intentionally narrow.

Future interpretation capabilities may expand only through explicit governed
work.

## Non-blocking ambiguity

A request for the "best" option without criteria may be recorded as a
non-blocking preference ambiguity.

It does not automatically stop processing.

## Determinism

Identical supported inputs produce identical:

- intent type;
- interpreted intent;
- ambiguity records;
- clarification decision;
- clarification questions.

No random arbitration is used.

## Relationship to adaptive reasoning

Intent interpretation precedes adaptive reasoning.

A clarification-blocked interpretation must not enter adaptive reasoning.

WO-INTENT-001 does not:

- construct `ReasoningRequest`;
- invoke `AdaptiveReasoningCycle`;
- select DIRECT / VERIFY / BRANCH / SEARCH;
- generate reasoning candidates;
- evaluate candidates;
- perform convergence.

That integration belongs to later governed work.

## Hard architecture boundaries

- intent interpretation != planning
- intent interpretation != adaptive reasoning
- intent interpretation != approval
- intent interpretation != execution
- intent interpretation != governed verdict
- clarification != reasoning escalation
- clarification != external research
- clarification != tool invocation
- clarification != user profiling
- inference != explicit user statement
- EXECUTE_REQUEST != execution authority
- no confidence percentage
- no probability claim
- no persistent cognitive memory
