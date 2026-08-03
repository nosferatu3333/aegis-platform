# AEGIS MVP Functional Proof - Domain D

Domain D verifies execution, conformance, evidence reconciliation, provenance,
and trace continuity for AEGIS Platform 1.7.0 RC1.

## Scenarios

- `AEGIS-RC1-S12`: successful simulated execution and verified evidence;
- `AEGIS-RC1-S13`: controlled failure and preserved failure evidence;
- `AEGIS-RC1-S14`: invalid non-terminal receipt rejection;
- `AEGIS-RC1-S15`: provenance-hash mismatch after controlled mutation;
- `AEGIS-RC1-S16`: request-to-evidence trace continuity.

## S12 and S13

The production execution engine emits deterministic simulated receipts.
Conformance verifies request identity, mission, capability, planned workflow,
ordering, terminal completeness, and the simulation boundary.

Reconciliation maps completed work to a complete result and controlled failure
to a failed result. A failed execution is never promoted to complete.

## S14 boundary

The production reconciler accepts only terminal receipts with timestamps and
canonical plan lineage. S14 changes a completed receipt to the non-terminal
`running` state and proves that reconciliation rejects it without emitting a
result.

This is a reconciliation-boundary proof, not a general external-effect
validator.

## S15 boundary

The production reconciler records SHA-256 content hashes in evidence
provenance. RC1 does not expose an automatic post-reconciliation integrity
verifier.

S15 therefore uses the exact production serialization and hashing method to
show:

1. the stored hash matches the original receipt;
2. a controlled mutation changes the digest;
3. the stored evidence no longer matches the mutated receipt.

## S16

The cognitive trace must preserve:

```text
request --planned_from--> plan
plan --resulted_in--> result
result --supported_by--> every evidence record
```

## Run

```powershell
python -m aegis_os.proof.domain_d
```

Run one scenario:

```powershell
python -m aegis_os.proof.domain_d --scenario AEGIS-RC1-S15
```

Generated evidence is written below:

```text
artifacts/functional-proof/domain-d/
```

All execution in this proof is deterministic simulation. Evidence proves what
Platform observed internally; it does not prove external real-world effects or
production readiness.
