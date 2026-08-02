# AEGIS Platform Distribution and Integrity

AEGIS Platform 1.0.0 adds a reproducible operator source bundle with embedded provenance and integrity verification.

## Build

The builder refuses a dirty Git worktree. From a clean release checkout:

```powershell
python scripts/build_distribution.py --output-dir dist
```

The output is `dist/aegis-platform-1.0.0.zip`.

## Verify

```powershell
python scripts/build_distribution.py --verify dist/aegis-platform-1.0.0.zip
```

A valid package reports `Distribution: verified` and the source commit from which it was created.

## Bundle contract

Every bundle contains:

- the tracked Platform source tree under `aegis-platform/`;
- `DISTRIBUTION_MANIFEST.json`, containing version, commit, tree, branch, file sizes, and SHA-256 hashes;
- `SHA256SUMS`, covering every tracked source file and the distribution manifest.

ZIP member ordering, timestamps, permissions, and JSON serialization are deterministic. Two bundles produced from the same clean commit are byte-identical.

## Security boundary

Verification proves that the bundle matches its embedded manifest and checksums. It does not establish publisher identity, replace code review, or prove real-world execution effects. A future signing work order may bind the bundle digest to a trusted release identity.
