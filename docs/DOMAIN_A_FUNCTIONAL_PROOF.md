# AEGIS MVP Functional Proof — Domain A

Domain A verifies request interpretation and capability routing for AEGIS
Platform 1.7.0 RC1.

## Scenarios

- `AEGIS-RC1-S01`: analysis-only mission;
- `AEGIS-RC1-S02`: positive live OPS capability match;
- `AEGIS-RC1-S03`: competing capability ranking;
- `AEGIS-RC1-S04`: no positive live OPS capability match.

## S03 evidence boundary

The live OPS registry currently contains only one capability. S03 therefore
uses two valid in-memory capability objects with the real production
`CapabilitySelector`.

This proves selector ranking semantics without changing or registering a fake
production OPS capability.

It is selector-contract proof, not live-registry competition proof.

## Run all Domain A scenarios

Set the OPS path:

`C:\Users\Woolis Shop\Projects\aegis-ops = "C:\Users\Woolis Shop\Projects\aegis-ops"`

Run the suite:

`python -m aegis_os.proof.domain_a`

## Run one scenario

`python -m aegis_os.proof.domain_a --scenario AEGIS-RC1-S02`

## Evidence

Generated evidence is written beneath:

`artifacts/functional-proof/domain-a/`

Generated evidence is ignored by Git and is not a signed release artifact.

## Declared RC1 boundary

Domain A proves deterministic request interpretation and routing behavior. It
does not prove unrestricted real-world execution, production readiness, or
autonomous repository modification.
