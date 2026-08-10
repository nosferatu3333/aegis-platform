# AEGIS Outcome / Constraint Model

## WO-INTENT-002

WO-INTENT-002 establishes CMP03 — Outcome Model.

The Outcome Model consumes a **sufficient** `IntentInterpretation`.

A `CLARIFICATION_REQUIRED` interpretation is not eligible for outcome modeling.

## Purpose

An outcome describes the state the user is trying to reach.

An outcome is not:

- the raw request;
- the interpreted intent;
- a plan;
- project state;
- a reasoning result;
- a candidate path;
- an approval;
- execution authority;
- a governed verdict.

## Outcome Model

`OutcomeModel` contains exactly six dimensions:

1. `intent_ref`
2. `desired_state`
3. `success_conditions`
4. `explicit_constraints`
5. `inferred_constraints`
6. `outcome_uncertainties`

## Intent reference

`intent_ref` anchors the model to the interpretation that produced it.

The Outcome Model does not reinterpret the original user request.

## Desired state

`desired_state` describes the state that should become true.

The minimum implementation uses the normalized interpreted intent as the
bounded desired-state representation.

This does not create a plan.

## Success conditions

Success conditions describe observable completion criteria.

They do not prescribe implementation steps.

They do not themselves validate completion.

They do not grant execution permission.

The model does not fabricate numerical targets or success criteria.

An empty success-condition set is valid.

## Explicit constraints

Explicit constraints remain user-originated and are preserved from the intent
layer.

## Inferred constraints

Inferred constraints remain separately identifiable from explicit constraints.

Inference does not become explicit user instruction merely because the system
records it.

## Outcome uncertainty

`outcome_uncertainties` preserves unresolved uncertainty without manufacturing
certainty.

Uncertainty does not automatically invalidate the outcome.

## Constraint conflict

CMP03 may preserve conflicting constraints.

It does not silently discard or resolve them.

Conflict resolution belongs to later reasoning or project coordination.

## Relationship to INTENT-001

CMP01 — Intent Interpreter remains unchanged.

CMP02 — Clarification Engine remains unchanged.

Only `SUFFICIENT` intent interpretations may continue into CMP03.

## Relationship to adaptive reasoning

WO-INTENT-002 does not:

- construct `ReasoningRequest`;
- select DIRECT / VERIFY / BRANCH / SEARCH;
- generate candidates;
- evaluate candidates;
- perform convergence;
- invoke `AdaptiveReasoningCycle`.

Outcome-to-reasoning mapping belongs to later system integration.

## Architecture boundaries

- outcome != raw request
- outcome != intent
- outcome != plan
- outcome != project state
- outcome != reasoning result
- outcome != candidate path
- outcome != approval
- outcome != execution authority
- outcome != governed verdict
- constraint != authority
- constraint != action
- success condition != execution permission
- no tool invocation
- no external network
- no persistent cognitive memory
