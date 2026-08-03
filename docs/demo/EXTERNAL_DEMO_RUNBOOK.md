# AEGIS External MVP Demonstration Runbook

## Demonstration boundary

AEGIS Platform 1.7.0-rc1 demonstrates governed cognitive workflow orchestration with live AEGIS OPS capability selection. Execution remains deterministic simulation only. The release does not claim verified real-world side effects.

## Operator sequence

1. Verify the signed release candidate with the included public key, trust policy, transparency ledger, and trust report.
2. Run `python -m aegis_os doctor` and `python -m aegis_os ready`.
3. Start the local dashboard with `python -m aegis_os serve`.
4. Select the live OPS development scenario and show capability score, matched evidence, and rationale.
5. Run an analysis-only scenario and show that no execution occurs.
6. Run an approval-required scenario and show that AEGIS pauses without inventing authority.
7. Run a bounded simulated execution and show evidence, reconciliation, and the final operator verdict.

## Required claims

- Capability selection comes from the live sibling AEGIS OPS repository when available.
- Authority requirements are explicit and cannot be silently bypassed.
- Every execution state is linked to evidence and reconciliation.
- Release integrity and provenance are independently verifiable.

## Prohibited claims

- Autonomous real-world execution.
- Verified external side effects.
- Production availability, multi-tenant security, or commercial SLA readiness.
