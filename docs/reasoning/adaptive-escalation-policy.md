# AEGIS Adaptive Escalation Policy

## WO-REASON-002 scope

WO-REASON-002 introduces deterministic selection of the minimum sufficient
reasoning mode for a bounded `ReasoningRequest`.

The canonical modes remain:

- `DIRECT`
- `VERIFY`
- `BRANCH`
- `SEARCH`

The policy decides cognitive effort only.

It does not execute the operation associated with the selected mode.

## Policy hierarchy

The policy evaluates escalation in this order:

1. `SEARCH`
2. `BRANCH`
3. `VERIFY`
4. `DIRECT`

The first satisfied mode becomes the selected mode.

This ordering ensures that stronger evidence or structural requirements are not
silently reduced to a weaker reasoning mode.

## DIRECT

`DIRECT` is selected when no stronger escalation trigger exists.

It means bounded reasoning is sufficient for the current request.

It does not mean:

- the request is unimportant;
- the outcome is low-value;
- execution is authorized;
- evidence is unnecessary in every downstream context.

## VERIFY

`VERIFY` is selected when uncertainty or risk is present but the request does
not require branching or external evidence acquisition.

`VERIFY` means verification is warranted before recommendation.

It does not itself perform verification or create evidence.

## BRANCH

`BRANCH` is selected when request structure indicates that multiple competing
reasoning paths are warranted.

Initial triggers include:

- explicit branch markers such as multiple approaches or competing options;
- material tradeoffs;
- ambiguous objectives;
- cross-domain complexity;
- multiple uncertainty signals with sufficient requested depth and budget;
- multiple constraints with sufficient requested depth and budget.

`BRANCH` does not generate candidate paths.

Candidate generation remains deferred to WO-REASON-003.

## SEARCH

`SEARCH` is selected when request signals explicitly indicate that external
evidence acquisition is required and the bounded reasoning budget is sufficient
for search-level deliberation.

Initial markers include:

- external evidence;
- external source;
- current information;
- current data;
- web research;
- research required;
- source verification.

`SEARCH` does not perform web research or invoke tools.

Tool use remains governed downstream.

## Budget and depth

`requested_depth` and `budget` constrain cognitive effort.

They do not create authority.

They do not create execution permission.

Depth alone does not force branching.

Budget alone does not force escalation.

## Semantic boundaries

The following invariants remain mandatory:

- reasoning mode != authority;
- reasoning mode != execution permission;
- `DIRECT` != low importance;
- `VERIFY` != evidence;
- `BRANCH` != candidate generation;
- `SEARCH` != external search execution;
- risk != prohibition;
- reasoning budget != authorization;
- reasoning result != governed verdict.

## Deferred work

WO-REASON-002 does not implement:

- candidate generation;
- candidate evaluation;
- convergence;
- external search execution;
- tool invocation;
- authority expansion;
- execution expansion;
- persistent cognitive memory;
- API integration;
- user-interface integration.

Candidate generation remains the responsibility of WO-REASON-003.
