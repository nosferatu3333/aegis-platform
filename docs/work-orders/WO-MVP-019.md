# WO-MVP-019 — Operator Trial Remediation

## Evidence basis

The Windows WO-MVP-018 rehearsal exposed a clean-install blocker: the attestation module imported `cryptography`, but the release requirements did not install it. A manual unconstrained install selected cryptography 50.0.0, outside Platform's declared `>=43,<47` range. The first failed bootstrap also produced no audit artifact.

## Remediation

- Add `cryptography>=43,<47` to the release dependency surface.
- Run `pip check` before runtime diagnostics.
- Preserve a partial JSON report when the Windows wrapper fails before the Python trial report exists.
- Allow the wrapper to initialize a temporary trust policy from a supplied public key, so signed-release verification can be exercised without mutating the published release directory.
- Add regression tests for all remediation controls.
