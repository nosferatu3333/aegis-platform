# AEGIS Platform Operator Handoff

## Supported release

AEGIS Platform 0.8.0 requires AEGIS Core `>=0.3.0,<0.4.0` and Python 3.11 or newer.

## Windows one-command workflow

```powershell
.\scripts\operator.ps1 bootstrap -CorePath "C:\path\to\aegis-core"
.\scripts\operator.ps1 ready
.\scripts\operator.ps1 serve
```

## Linux/macOS one-command workflow

```sh
./scripts/operator.sh bootstrap --core-path ../aegis-core
./scripts/operator.sh ready
./scripts/operator.sh serve
```

## Acceptance and recovery

Run `acceptance` before demonstration and `validate` before release or handoff. If readiness is blocked, run `doctor`, correct the failed check, and repeat `ready`. Roll back by restoring the previous tagged repository archive and recreating `.venv`.

## Operational boundary

This release executes deterministic simulations only. It does not verify real-world side effects.
