# External MVP Release Candidate

WO-MVP-022 freezes the first externally demonstrable AEGIS Platform MVP release candidate.

The release-candidate builder produces a single verification directory containing:

- reproducible Platform distribution ZIP;
- detached Ed25519 provenance attestation and signature;
- public verification key;
- explicit signing trust policy;
- append-only transparency ledger;
- human-readable/machine-readable trust report;
- governed five-scenario acceptance report;
- release-candidate manifest tying all artifacts to one source commit and tree.

Build command:

```powershell
python scripts/build_release_candidate.py --output-dir ".\release-candidate" --private-key "C:\secure\aegis-release-private.pem" --public-key "C:\secure\aegis-release-public.pem"
```

For a rehearsal-only key pair, add `--generate-key`. Never distribute the private key. The generated release remains bounded to deterministic simulation and does not claim real-world effects.
