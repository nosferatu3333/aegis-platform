# AEGIS Candidate Path Generation

## WO-REASON-003 scope

WO-REASON-003 introduces bounded generation of materially distinct candidate
reasoning paths after `BRANCH` reasoning has already been selected.

Candidate generation is not adaptive escalation. The escalation policy remains
responsible for deciding whether branching is warranted.

## CandidatePath

A `CandidatePath` is a descriptive reasoning structure containing:

- candidate identifier;
- intent reference;
- outcome reference;
- approach label;
- approach summary;
- primary objective;
- assumptions;
- acknowledged constraints;
- evidence needs;
- known uncertainty.

A candidate path is not:

- a score;
- a ranking;
- a recommendation;
- a governed verdict;
- an approval;
- an executable plan.

## CandidatePathGenerator

`CandidatePathGenerator` produces deterministic candidate paths for
`ReasoningMode.BRANCH` only.

Generation is rejected for other reasoning modes.

## Candidate bounds

Candidate count is explicitly bounded:

- minimum: 2;
- default: 3;
- maximum: 5.

Recursive or unbounded candidate generation is not authorized.

## Initial approach families

The bounded generator uses five materially different reasoning structures:

1. Constraint-First
2. Evidence-First
3. Direct-Outcome
4. Risk-First
5. Dependency-First

These are reasoning approaches, not personas.

They do not represent simulated agents, council members, identities, or votes.

## Context-sensitive ordering

Candidate families are deterministically prioritized from request structure:

- explicit constraints prioritize Constraint-First;
- uncertainty prioritizes Evidence-First;
- risk signals prioritize Risk-First;
- Direct-Outcome provides a bounded minimal-path alternative;
- Dependency-First provides a sequencing-oriented alternative.

The output order is deterministic for identical bounded inputs.

## Material distinctness

Candidate distinctness refers to differences in reasoning structure and primary
objective.

Changing wording alone does not constitute a distinct candidate path.

The generator rejects internally duplicated candidate signatures.

## Shared intent

Every generated candidate preserves the same:

- intent reference;
- outcome reference.

Branching therefore explores alternative approaches to the same objective
rather than silently changing the objective.

## Semantic boundaries

The following invariants remain mandatory:

- candidate generation != candidate evaluation;
- candidate generation != ranking;
- candidate generation != recommendation;
- candidate generation != convergence;
- candidate generation != authority;
- candidate generation != execution permission;
- candidate generation != tool invocation;
- candidate generation != external search execution;
- candidate path != persona;
- distinctness != paraphrasing;
- candidate count is bounded;
- persistent cognitive memory remains unauthorized.

## Deferred work

WO-REASON-003 does not implement:

- candidate scoring;
- candidate comparison;
- candidate ranking;
- candidate rejection;
- candidate selection;
- convergence;
- tool execution;
- external search execution;
- authority expansion;
- execution expansion;
- persistent cognitive memory.

Candidate evaluation remains the responsibility of WO-REASON-004.

Convergence remains the responsibility of WO-REASON-005.
