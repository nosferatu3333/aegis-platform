# Fresh-Machine Operator Trial

WO-MVP-018 supplies a deterministic deployment rehearsal for a clean Windows operator environment.

## Scope

The trial records runtime diagnostics, launch readiness, five governed acceptance scenarios, occupied-port blocking, optional cryptographic trust verification, execution timing, friction, and recovery commands.

It does not claim that a specific external computer has passed until the script is executed on that computer and its generated report is retained.

## Windows execution

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\operator_trial.ps1 -CorePath "C:\Users\Woolis Shop\Projects\aegis-core-clean"
```

With release trust artifacts:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\operator_trial.ps1 -CorePath "C:\Users\Woolis Shop\Projects\aegis-core-clean" -Bundle ".\release\aegis-platform.zip" -Attestation ".\release\aegis-platform.zip.attestation.json" -Signature ".\release\aegis-platform.zip.attestation.sig" -Policy ".\release\trust-policy.json" -Ledger ".\release\transparency.jsonl"
```

## Acceptance

A passing report requires all exercised checks to pass. Omitting trust artifacts is reported as friction but does not fail the runtime rehearsal. Supplying only a partial trust-artifact set fails explicitly.
