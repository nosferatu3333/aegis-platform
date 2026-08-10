# AEGIS Convergence Controller

## WO-REASON-005 scope

WO-REASON-005 introduces bounded deterministic resolution of already-generated
and already-evaluated reasoning candidates.

The controller consumes:

- one `ReasoningRequest`;
- a tuple of `CandidatePath` objects;
- a tuple of corresponding `CandidateEvaluation` objects.

It does not generate or reevaluate candidates.

## Convergence states

Three terminal states exist:

- `RESOLVED`
- `TIED`
- `INSUFFICIENT`

### RESOLVED

Exactly one candidate has the highest aggregate score and passes all active
sufficiency gates.

The result may expose that candidate as `preferred_candidate_id`.

A preferred candidate is a reasoning preference only.

It is not:

- approval;
- authority;
- execution permission;
- governed verdict;
- tool authorization.

### TIED

Multiple candidates share the highest aggregate score.

No positional, lexical, random, or hidden tie-breaker is authorized.

A tie remains unresolved.

### INSUFFICIENT

Exactly one candidate leads by aggregate score, but the active request context
shows that the leader fails a material sufficiency gate.

The initial gates are:

- evidence readiness when evidence pressure exists;
- uncertainty exposure when uncertainty exists;
- risk exposure when risk exists.

A score of `0` or `1` on the relevant dimension blocks resolution.

## Identifier integrity

Candidate identifiers must be unique.

Evaluation identifiers must be unique.

The candidate identifier set and evaluation identifier set must match exactly.

At least two candidates are required.

## Stopping rule

Convergence is bounded and non-recursive.

The controller returns one terminal result and stops.

It does not:

- generate a new candidate;
- perform a second evaluation pass;
- recursively call convergence;
- request external search;
- invoke tools.

Any future continuation after `TIED` or `INSUFFICIENT` belongs to a higher-level
adaptive cycle and remains deferred to WO-REASON-006.

## Aggregate semantics

The aggregate score was created by WO-REASON-004.

WO-REASON-005 consumes it.

It does not reinterpret the aggregate as probability, confidence, truth, or
authority.

A unique aggregate leader is necessary for resolution but is not sufficient
when an active sufficiency gate fails.

## Semantic boundaries

The following invariants remain mandatory:

- convergence != candidate generation;
- convergence != candidate evaluation;
- convergence != approval;
- convergence != authority;
- convergence != execution permission;
- convergence != governed verdict;
- convergence != tool invocation;
- convergence != external search execution;
- preferred candidate != authority;
- preferred candidate != execution permission;
- aggregate score != probability;
- aggregate score != confidence;
- ties remain unresolved;
- insufficient support remains unresolved;
- no arbitrary tie-breaking;
- no input-order tie-breaking;
- no persona / judge / council simulation;
- no persistent cognitive memory;
- convergence is bounded and non-recursive.

## Deferred work

WO-REASON-005 does not implement:

- adaptive retry;
- candidate regeneration;
- reevaluation;
- external evidence acquisition;
- tool use;
- execution;
- authority expansion;
- persistent memory.

Integrated adaptive orchestration remains the responsibility of
WO-REASON-006.
