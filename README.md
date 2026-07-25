# AEGIS Platform

AEGIS Platform is the developing product and operational control plane for
AEGIS OS. It currently contains a limited, simulated vertical slice used to
characterize product integration while `aegis-core` becomes the canonical
cognitive authority.

## Current responsibility

Platform is expected to own:

- Public APIs and future SDK delivery.
- Authentication, tenancy, users, and workspaces.
- Human approvals and escalation interfaces.
- Studio and voice-to-flux presentation.
- Runtime operations, observability, budgets, and deployment configuration.

Platform must not become an independent cognitive brain. Canonical intent,
decision, planning, execution-result, evaluation, policy, memory-write, and
audit semantics belong to `aegis-core`.

## Prototype status

The current Python package is a stabilization prototype:

- Agent outputs are simulations.
- Decision scores use a string-length heuristic.
- Evaluation metrics are fixed heuristic values.
- Planning decomposes tasks but does not execute every task.
- Learning observations are not validated across runs and are not promoted to
  canonical learning.

These limitations are deliberately visible in returned data and tests.

## Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m unittest discover -s . -p "test_*.py" -v
python -m aegis_os.main
```

See `docs/stabilization-phase-2-5.md` for the repaired baseline and migration
constraints.
