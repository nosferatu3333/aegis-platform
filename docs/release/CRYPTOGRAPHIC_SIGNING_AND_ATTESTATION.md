# Cryptographic Release Signing and Provenance Attestation

AEGIS Platform distributions can be signed with Ed25519 after deterministic bundle verification. Signing produces two detached files:

- `<bundle>.attestation.json` — canonical provenance statement;
- `<bundle>.attestation.sig` — Base64-encoded Ed25519 signature over the exact attestation bytes.

The private key is never embedded in the repository or distribution. Store it outside the project and protect it with the operating system's secret-management controls.

## Generate a key pair

```powershell
python -m aegis_os keygen `
  --private-key C:\secure\aegis-release-private.pem `
  --public-key C:\secure\aegis-release-public.pem
```

## Sign a verified distribution

```powershell
python -m aegis_os sign-package dist\aegis-platform-1.0.0.zip `
  --private-key C:\secure\aegis-release-private.pem
```

The signer refuses to attest a bundle that fails the embedded distribution inventory.

## Verify publisher provenance

```powershell
python -m aegis_os verify-attestation dist\aegis-platform-1.0.0.zip `
  --attestation dist\aegis-platform-1.0.0.zip.attestation.json `
  --signature dist\aegis-platform-1.0.0.zip.attestation.sig `
  --public-key C:\trusted\aegis-release-public.pem
```

Verification binds the exact bundle digest and size to its source commit, source tree, source branch, Platform version, and signer key identifier.

## Trust boundary

A valid signature proves that the holder of the corresponding private key signed the attestation. Publisher identity is only as trustworthy as the channel used to obtain and pin the public key. Key rotation, revocation publication, hardware-backed signing, and transparency-log publication remain separate operational controls.
