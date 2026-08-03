# Release Transparency and Verification

AEGIS Platform records release and signing-key lifecycle events in an append-only JSON Lines ledger. Each event contains the previous event hash and its own SHA-256 digest, making deletion, reordering, or modification detectable.

## Commands

```powershell
python -m aegis_os transparency-append --ledger transparency.jsonl --event-type release-published --subject v1.2.0 --details-json '{"commit":"..."}'
python -m aegis_os transparency-verify --ledger transparency.jsonl
python -m aegis_os trust-report bundle.zip --attestation bundle.zip.attestation.json --signature bundle.zip.attestation.sig --policy trust-policy.json --ledger transparency.jsonl
```

A `TRUSTED` verdict requires valid package integrity, a valid signature, a trusted signer under the current policy, and a valid ledger when one is supplied.
