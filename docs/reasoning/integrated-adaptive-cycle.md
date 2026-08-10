# AEGIS Integrated Adaptive Reasoning Cycle

## WO-REASON-006 scope

WO-REASON-006 composes the reasoning capabilities introduced by
WO-REASON-001 through WO-REASON-005 into one bounded adaptive cycle.

The cycle begins from one `ReasoningRequest`.

It first invokes the existing `AdaptiveEscalationPolicy`.

The selected mode determines the authorized reasoning path.

## Modes

### DIRECT

`DIRECT` returns immediately.

The integrated cycle does not manufacture candidate competition when the
escalation policy did not request branching.

No candidate generation, evaluation, or convergence is performed.

### VERIFY

`VERIFY` means additional verification is required.

WO-REASON-006 does not perform external evidence acquisition.

It returns a bounded result indicating the verification requirement and stops.

### BRANCH

`BRANCH` executes the existing bounded reasoning pipeline:

`CandidatePathGenerator`
→ `CandidateEvaluator`
→ `ConvergenceController`

The convergence result remains one of:

- `RESOLVED`
- `TIED`
- `INSUFFICIENT`

`RESOLVED` is a reasoning preference only.

It is not approval, authority, execution permission, or a governed verdict.

### SEARCH

`SEARCH` means external research or search is required.

WO-REASON-006 does not perform network search and does not invoke tools.

It returns a bounded result indicating the search requirement and stops.

## Result contract

`AdaptiveCycleResult` contains exactly:

- selected reasoning mode;
- generated candidates, when BRANCH;
- candidate evaluations, when BRANCH;
- convergence result, when BRANCH;
- a human-readable bounded reason.

Non-BRANCH results contain no candidate, evaluation, or convergence artifacts.

## Determinism

Identical requests and identical component state produce identical cycle
results.

No random arbitration, hidden retry, or recursive adaptive cycle is
authorized.

## Stopping behavior

DIRECT:

stop after escalation.

VERIFY:

stop after escalation.

SEARCH:

stop after escalation.

BRANCH:

stop after generation, evaluation, and one convergence pass.

There is no automatic second pass.

TIED remains unresolved.

INSUFFICIENT remains unresolved.

Higher-level continuation after VERIFY, SEARCH, TIED, or INSUFFICIENT belongs
to later orchestration and evidence/tool coordination work.

## Hard architecture boundaries

- adaptive cycle != authority
- adaptive cycle != approval
- adaptive cycle != execution permission
- adaptive cycle != governed verdict
- adaptive cycle != tool invocation
- adaptive cycle != external search execution
- DIRECT != hidden BRANCH
- VERIFY != external verification execution
- SEARCH != external search execution
- RESOLVED != approved
- RESOLVED != executable
- preferred candidate != authority
- no forced winner
- no recursive adaptive cycle
- no hidden retry loop
- no persona / judge / council simulation
- no confidence percentage
- no probability claim
- no persistent cognitive memory

## Existing contracts remain protected

WO-REASON-006 does not modify:

- `ReasoningRequest`
- `ReasoningResult`
- `ReasoningController`
- `AdaptiveEscalationPolicy`
- `CandidatePathGenerator`
- `CandidateEvaluator`
- `ConvergenceController`

It composes those capabilities without redefining them.

## Deferred work

WO-REASON-006 does not implement:

- external verification;
- web/network research;
- evidence acquisition;
- capability or tool coordination;
- operational execution;
- authority expansion;
- governed verdict expansion;
- persistent cognitive memory;
- recursive autonomous deliberation.

Those concerns remain outside the adaptive reasoning cycle.
