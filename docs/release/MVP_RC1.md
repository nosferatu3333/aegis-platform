# AEGIS Platform MVP RC1

## Release boundary

RC1 packages the governed MVP chain from canonical capability selection through bounded planning, authority gating, deterministic simulation, conformance, evidence, reconciliation, and the dashboard demonstration surface.

This release does **not** perform external actions or prove real-world effects.

## Supported compatibility

- Python: 3.11 or newer
- AEGIS Core: `>=0.3.0,<0.4.0`
- AEGIS Platform: `0.7.0`

The public Python package name `aegis-core` may resolve to an unrelated package from a public index. The supported local installation path is therefore the explicit sibling Core checkout installed by `scripts/bootstrap.py`.

## Reproducible local setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python scripts/bootstrap.py --core-path "C:\path\to\aegis-core"
```

The bootstrap process installs Core first, installs Platform without dependency resolution replacing Core, installs pinned release ranges, runs diagnostics, and executes the full test suite.

## One-command diagnostics and startup

```powershell
python -m aegis_os doctor
python -m aegis_os serve
```

Dashboard: `http://127.0.0.1:8000/`

## Release acceptance

A release candidate is acceptable only when:

1. `python -m aegis_os doctor` reports `ready`.
2. `python scripts/validate.py` passes.
3. The full test suite passes.
4. The worktree is clean.
5. Manual governed scenarios confirm analyzed, paused, denied, completed, and failed outcomes.

## Rollback

1. Stop the local server.
2. Preserve logs and the failing commit identifier.
3. Check out the previously accepted Platform tag or archive.
4. Recreate the virtual environment.
5. Run `scripts/bootstrap.py` against the compatible Core checkout.
6. Confirm diagnostics and tests before restarting.
