## 1.1.0

- Added signing-key trust policies with explicit active, retiring, and revoked states.
- Added deterministic key rotation lineage and validity windows.
- Added full and future-only revocation semantics.
- Added trust-policy-aware attestation verification and operator CLI commands.

## 1.0.0

- Add Ed25519 distribution signing and detached provenance attestations.
- Add key generation, signing, and attestation verification commands.
- Bind signed bundles to source commit, tree, branch, digest, size, version, and signer key ID.

## 0.9.0

- Added reproducible distribution bundles, source provenance, and offline integrity verification.

# Changelog

## 0.7.0 - MVP RC1 hardening

- Added explicit AEGIS Core compatibility diagnostics.
- Added reproducible sibling-repository bootstrap installation.
- Added one-command doctor and local server entry points.
- Added machine-readable release metadata, acceptance criteria, and rollback guidance.
- Added release-candidate regression coverage.

## 0.7.0 - Formal governed runtime MVP release

- Promoted MVP RC1 to the accepted `v0.7.0` release.
- Added deterministic governed acceptance scenarios covering analyzed, completed, paused, denied, and failed outcomes.
- Added machine-readable formal release status, tag, and acceptance commands.
- Added the formal v0.7.0 release page and explicit simulation boundary.
