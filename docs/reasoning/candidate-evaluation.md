# AEGIS Candidate Evaluation

## WO-REASON-004 scope

WO-REASON-004 introduces deterministic evaluation of already-generated
`CandidatePath` objects against an explicit structural rubric.

Evaluation occurs after candidate generation.

It does not generate additional candidate paths.

## Inputs

`CandidateEvaluator` receives:

- the bounded `ReasoningRequest`;
- a tuple of already-generated `CandidatePath` objects.

Candidate intent and outcome references must match the request.

Candidate identifiers must be unique.

## CandidateEvaluation

Each immutable evaluation contains:

- candidate identifier;
- constraint alignment;
- evidence readiness;
- uncertainty exposure;
- risk exposure;
- dependency burden;
- directness;
- aggregate score;
- strengths;
- limitations.

No selection, recommendation, authority, execution, or verdict field exists.

## Score contract

Each dimension is an integer from `0` through `4`.

`0` means weakest alignment for that criterion.

`4` means strongest alignment for that criterion.

The aggregate score is the arithmetic sum of the six dimension scores and
therefore ranges from `0` through `24`.

The aggregate is descriptive only.

Aggregate score != winner.

Aggregate score != recommendation.

Aggregate score != authority.

Aggregate score != execution permission.

## Explicit structural rubric

The initial evaluator uses inspectable structural rules.

### Constraint alignment

When no explicit constraints exist, all supported paths receive `4`.

When constraints exist:

- `Constraint-First` receives `4` when all constraints are acknowledged;
- another supported path receives `3` when all constraints are acknowledged;
- partial acknowledgement receives `2`;
- no acknowledgement receives `0`.

### Evidence readiness

When no uncertainty or risk creates evidence pressure, the score is `4`.

Otherwise:

- `Evidence-First`: `4`;
- a candidate carrying explicit evidence needs: `3`;
- `Risk-First` or `Dependency-First` without explicit evidence needs: `2`;
- remaining paths: `1`.

### Uncertainty exposure

Higher scores mean lower unresolved uncertainty exposure.

When no uncertainty exists, all paths receive `4`.

When uncertainty exists:

- `Evidence-First`: `4`;
- `Constraint-First`: `2`;
- `Risk-First`: `2`;
- `Dependency-First`: `2`;
- `Direct-Outcome`: `1`.

### Risk exposure

Higher scores mean lower unmanaged risk exposure.

When no risk signal exists, all paths receive `4`.

When risk exists:

- `Risk-First`: `4`;
- `Dependency-First`: `3`;
- `Constraint-First`: `2`;
- `Evidence-First`: `2`;
- `Direct-Outcome`: `1`.

### Dependency burden

Higher scores mean lower unresolved dependency burden.

- `Dependency-First`: `4`;
- `Direct-Outcome`: `3`;
- `Constraint-First`: `2`;
- `Evidence-First`: `2`;
- `Risk-First`: `2`.

### Directness

- `Direct-Outcome`: `4`;
- `Constraint-First`: `3`;
- `Evidence-First`: `2`;
- `Risk-First`: `2`;
- `Dependency-First`: `2`.

## Strengths and limitations

A dimension is exposed as a strength when its score is `3` or `4`.

A dimension is exposed as a limitation when its score is `0` or `1`.

Scores of `2` remain neutral comparison signals.

These labels are descriptive projections of the explicit rubric.

They are not hidden model judgments.

## Candidate order

Evaluation preserves input candidate order.

The evaluator does not sort candidates by aggregate score.

Ties remain valid.

## Semantic boundaries

The following invariants remain mandatory:

- candidate evaluation != candidate generation;
- candidate evaluation != ranking;
- candidate evaluation != final selection;
- candidate evaluation != recommendation;
- candidate evaluation != convergence;
- candidate evaluation != authority;
- candidate evaluation != execution permission;
- candidate evaluation != tool invocation;
- candidate evaluation != external search execution;
- evaluation score != authority;
- evaluation score != execution permission;
- evaluation record != governed verdict;
- evaluation record != executable plan;
- evaluation criteria are explicit and inspectable;
- ties are valid;
- personas / simulated judges are not used;
- persistent cognitive memory remains unauthorized.

## Deferred work

WO-REASON-004 does not implement:

- ranking;
- candidate rejection;
- candidate selection;
- final recommendation;
- convergence;
- tool execution;
- external search execution;
- authority expansion;
- execution expansion;
- persistent cognitive memory.

Convergence and final candidate resolution remain the responsibility of
WO-REASON-005.
