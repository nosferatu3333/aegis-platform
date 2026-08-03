# Domain F Functional Proof — Release Integrity and Trust

Domain F closes the 20-scenario AEGIS RC1 proof track with two executable release-verification scenarios.

## S19 — Valid signed RC1 distribution

S19 verifies the preserved official RC1 package using only published release material and production verification contracts:

- exact outer-package SHA-256 identity;
- embedded distribution manifest and `SHA256SUMS` verification;
- detached Ed25519 attestation verification;
- signing trust-policy enforcement;
- transparency-ledger hash-chain verification;
- recomputed composed trust report;
- agreement between the published and recomputed trust reports;
- bounded release-acceptance claims.

The scenario extracts the official package only into temporary storage. It does not rebuild, sign, publish, or modify the release, and it does not access private signing material.

## S20 — Tampered distribution rejection

S20 copies the signed inner distribution into temporary storage and modifies one payload entry. The original attestation, signature, public trust policy, and transparency ledger remain unchanged.

The controlled copy must be rejected by:

- the embedded distribution verifier;
- detached attestation verification;
- trust-policy verification;
- the composed trust report.

The transparency ledger remains valid because it was not modified; this does not override the integrity failure. The final trust verdict must still be `REJECTED`.

The official outer package and original inner bundle are hashed before and after the scenario to prove they remain unchanged.

## Trust boundary

A successful S19 proves that the preserved RC1 bytes match the published distribution inventory, that the provenance attestation is cryptographically valid, that the signing key is accepted by the published policy, and that the transparency ledger is internally consistent.

It does not prove broad software safety, production readiness, real-world effects, or the absence of undiscovered defects. RC1 remains bounded to deterministic simulation claims.

## Required environment

The proof requires the preserved official package path:

```powershell
$env:AEGIS_RC1_RELEASE_PATH = "C:\path\to\aegis-platform-1.7.0-rc1-official.zip"
```

Run the aggregate proof:

```powershell
python -m aegis_os.proof.domain_f
```

Run one scenario:

```powershell
python -m aegis_os.proof.domain_f --scenario AEGIS-RC1-S19
python -m aegis_os.proof.domain_f --scenario AEGIS-RC1-S20
```

Generated evidence is written beneath `artifacts/functional-proof/domain-f/` and is not a signed release artifact.
