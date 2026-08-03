# Signing-Key Lifecycle and Trust Policy

AEGIS Platform 1.1.0 introduces an explicit trust-policy boundary for release signing keys. A valid Ed25519 signature is no longer sufficient by itself: the signer must also be present in the operator's trust policy and valid for the attestation issuance time.

## Initialize trust

```powershell
python -m aegis_os trust-init `
  --public-key .\aegis-release-public.pem `
  --policy .\aegis-signing-trust-policy.json
```

The policy embeds only public keys. Private signing material must remain outside the repository, distribution bundle, and trust-policy file.

## Rotate the active key

Generate the replacement key pair separately, then rotate:

```powershell
python -m aegis_os trust-rotate `
  --policy .\aegis-signing-trust-policy.json `
  --new-public-key .\aegis-release-public-v2.pem
```

Rotation marks the previous key as `retiring`, closes its signing window, records successor/predecessor lineage, and activates the replacement key. Historical signatures issued within the previous key's validity window remain verifiable.

## Revoke a key

For compromise, invalidate all signatures made by the key:

```powershell
python -m aegis_os trust-revoke `
  --policy .\aegis-signing-trust-policy.json `
  --key-id ed25519:... `
  --reason "private key compromise"
```

For routine retirement where older signatures should remain trusted, add `--future-only` and an explicit revocation time.

## Verify against trust policy

```powershell
python -m aegis_os verify-trusted-attestation `
  .\aegis-platform-1.0.0.zip `
  --attestation .\aegis-platform-1.0.0.zip.attestation.json `
  --signature .\aegis-platform-1.0.0.zip.attestation.sig `
  --policy .\aegis-signing-trust-policy.json
```

Verification requires both cryptographic validity and policy validity. Unknown signers, signatures outside a key's validity window, and revoked keys are rejected.

## Operational policy

- Keep one active signing key.
- Rotate before planned key retirement.
- Revoke immediately on suspected compromise.
- Distribute trust-policy updates through an authenticated channel.
- Retain old public keys only when historical verification remains intended.
- Never publish or commit private signing keys.

This policy is local and file-based. Hardware-backed keys, multi-party authorization, signed trust-policy updates, and transparency-log publication remain future controls.
