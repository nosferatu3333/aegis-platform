# AEGIS MVP Functional Proof - Domain C

Domain C verifies the authority and governance boundary for AEGIS Platform
1.7.0 RC1.

## Scenarios

- `AEGIS-RC1-S08`: valid full-scope authority permits simulated execution;
- `AEGIS-RC1-S09`: missing approval pauses before execution;
- `AEGIS-RC1-S10`: explicit denial overrides an otherwise valid grant;
- `AEGIS-RC1-S11`: incomplete grant scope pauses before execution.

## Canonical boundary

Every bounded step requires the plan scope and its individual step scope.
The authority gate evaluates immutable Core authority records and does not
create or infer approval.

An execution request is emitted only when every decision is `allow`.
Blocking decisions produce either `paused` or `denied` governed-runtime
results without an execution receipt.

## Run

```powershell
python -m aegis_os.proof.domain_c
```

Run one scenario:

```powershell
python -m aegis_os.proof.domain_c --scenario AEGIS-RC1-S10
```

Generated evidence is written beneath:

```text
artifacts/functional-proof/domain-c/
```

This proof covers deterministic simulated execution only. It does not claim
external real-world effects or production readiness.
