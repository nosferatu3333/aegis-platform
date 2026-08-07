# AEGIS MVP Demonstration Baseline

## Purpose

This document defines how a fresh operator demonstrates the current AEGIS MVP.

The demonstration is designed to make the existing cognitive and governance
boundaries visible. It does not claim autonomous real-world execution.

## Canonical operator journey

1. Start AEGIS with `python -m aegis_os serve`.
2. Verify the platform with `GET /health`.
3. Open the operator dashboard.
4. Define a mission or select a canonical demonstration.
5. Analyze the mission.
6. Inspect capability selection and its rationale.
7. Inspect the proposed sequence.
8. Inspect the authority or approval state.
9. Run simulation only when the selected demonstration permits it.
10. Inspect validation and evidence separately from execution.
11. Read the governed verdict and any stop condition.
12. Stop AEGIS with `Ctrl+C`.

## DEMO-A — Research / Analysis

Backend scenario:

`analysis-only-research`

Purpose:

Demonstrate interpretation, capability selection, planning, evidence, and a
governed result without requesting execution.

Required boundary:

`execute = false`

Direct simulated execution is disabled while this preset remains selected.

Expected governed outcome:

`analyzed`

## DEMO-B — Bounded Simulation

Backend scenario:

`live-ops-development`

Purpose:

Demonstrate the bounded lifecycle from mission analysis through deterministic
simulated execution, validation, evidence, and verdict.

Execution boundary:

Simulation only.

The demonstration must never represent simulated completion as a real-world
effect.

Expected governed outcome:

`completed`

## DEMO-C — Approval Gate

Backend scenario:

`approval-gated-change`

Purpose:

Demonstrate that capability and a technically valid plan do not imply
authority.

Authority requirement:

`approval_required`

Direct simulation is disabled for the preset so the demonstration is routed
through the governed runtime.

Without an explicit authority grant, the governed runtime must stop rather than
fabricate permission.

Expected governed outcome:

`paused`

## Semantic boundaries

The demonstration must preserve these distinctions:

- analysis is not execution;
- simulation is not real execution;
- capability is not authority;
- plan is not approval;
- evidence is not confidence;
- validation is not permission;
- verdict is not action;
- health is not mission success;
- proof is not execution;
- UI visibility is not runtime authority.

## What the operator should be able to explain

After the demonstration, a fresh operator should be able to identify:

- what mission was requested;
- what capability AEGIS selected;
- what sequence AEGIS proposed;
- whether execution was requested;
- whether authority existed;
- whether any execution shown was simulated;
- what validation checked;
- what evidence supports the displayed result;
- why the final governed verdict was produced;
- why a blocked or paused operation did not continue.

## Non-goals

This baseline does not add:

- autonomous tool execution;
- real-world side effects;
- persistent cognitive memory;
- multi-agent deliberation;
- learned capability routing;
- Risk-Triggered Deliberation;
- WO-REASON-001;
- new Core contracts;
- new OPS scope;
- new release authority.

The purpose of this baseline is demonstration clarity, not cognitive or
execution expansion.
