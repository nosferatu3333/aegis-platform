# AEGIS MVP Functional Proof — Domain E

Domain E verifies operational resilience at the boundary between AEGIS
Platform 1.7.0 RC1 and the sibling AEGIS OPS capability engine.

## Scenarios

- `AEGIS-RC1-S17`: OPS unavailable;
- `AEGIS-RC1-S18`: malformed capability input.

## S17 — OPS unavailable

The production `OpsCapabilitySelectorAdapter` identifies a missing OPS
capability directory and raises `OpsIntegrationError`. Its diagnostic remains
machine-readable:

```text
source: aegis-ops
available: false
error: <non-empty diagnostic>
```

The production `HybridCapabilitySelector` may then use its declared bounded
Platform fallback. The proof requires that the resulting analysis identifies
its source as `platform-bounded-fallback`; it must not claim that OPS selected
the capability.

The scenario performs no execution.

## S18 — malformed capability input

The proof enables the live OPS Python namespace and invokes the production:

- `CapabilityLoader`;
- `CapabilityRegistry`;
- `CapabilitySelector`.

A temporary malformed YAML capability is supplied. Rejection may occur as an
explicit loader exception or as a zero-valid-capability result. Both are valid
rejection modes only when:

- zero malformed capabilities are loaded;
- zero malformed capabilities enter the registry;
- selection receives zero candidates;
- planning and execution are not reached.

The real OPS repository and its capability modules are not modified.

## Declared RC1 boundary

RC1 exposes a typed availability diagnostic and bounded fallback. It does not
currently expose automatic retry policy, timeout policy, or a circuit breaker
for this integration. Domain E does not claim those mechanisms.

## Environment

Domain E requires the live OPS repository path:

```powershell
$env:AEGIS_OPS_PATH = "C:\Users\Woolis Shop\Projects\aegis-ops"
```

## Run

```powershell
python -m aegis_os.proof.domain_e
```

Run one scenario:

```powershell
python -m aegis_os.proof.domain_e --scenario AEGIS-RC1-S17
```

Generated evidence is written below:

```text
artifacts/functional-proof/domain-e/
```
