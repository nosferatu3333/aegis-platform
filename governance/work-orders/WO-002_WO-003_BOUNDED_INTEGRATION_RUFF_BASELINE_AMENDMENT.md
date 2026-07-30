# WO-002/WO-003 Bounded Integration Authorization — Ruff Baseline Amendment

**Amendment status:** AUTHORIZED — BOUNDED NO-REGRESSION RUFF BASELINE
**Date authorized:** 2026-07-30
**Original authorization:** `70305cf86c92944149fc337400848b44a0c80309`
**Preserved Integration A:** `fb0364d1b4e0a27953ea7d683a786193d6e61c48`
**Integration A tree:** `b165ad0521d8544f613fd9b1b95e541fd107805a`
**Protected base:** `c137005b08c449a8e19f7734098865dd10181955`
**Authorized owner:** Release & Integration Engineer
**Decision owner:** Documentation & Governance
**Policy scope:** This bounded integration only

---

## Purpose

This amendment replaces the absolute repository-wide Ruff-cleanliness gates in the original bounded integration authorization with an exact, evidence-backed no-regression policy.

Release & Integration proved that the repository-wide Ruff failure consists of three violations inherited unchanged from the protected base. The violating files are outside the 21-path integration boundary, retain their exact base blobs in Integration A, and were not introduced or modified by Integration A. Correcting them would violate the authorized path boundary.

This is a scoped validation exception under the Engineering Charter's failure-handling policy. It does not modify Ruff configuration, establish a repository-wide Infrastructure policy, reduce lint requirements for authorized paths, or authorize remediation of inherited debt.

## Preserved Integration State

| Control | Exact identity |
|---|---|
| Recovery tag | `recovery/pre-wo-002-wo-003-integration-c137005b` |
| Recovery tag object | `9406fc75ecd6ddc5ef45adeff4042587dfdb2bf8` |
| Protected base | `c137005b08c449a8e19f7734098865dd10181955` |
| Integration branch | `integration/wo-002-wo-003-c137005b` |
| Integration A | `fb0364d1b4e0a27953ea7d683a786193d6e61c48` |
| Integration A tree | `b165ad0521d8544f613fd9b1b95e541fd107805a` |
| Integration A parent | `c137005b08c449a8e19f7734098865dd10181955` |

Integration A contains exactly the authorized nine paths, and every Integration A path blob matches WO-002 source `4d1842087289336675d43d7cd650bd80f57b8c8d`.

Integration A must not be recreated, amended, reset, replaced, rebased, or supplemented with an intermediate commit.

## Exact Inherited Ruff Baseline

The authoritative inherited baseline is the following exact normalized diagnostic set:

| Relative path | Location | Rule | Diagnostic |
|---|---:|---|---|
| `aegis_os/knowledge/knowledge_graph.py` | `1:40` | `F401` | `aegis_os.knowledge.concept.Concept` imported but unused |
| `aegis_os/knowledge/knowledge_graph.py` | `2:45` | `F401` | `aegis_os.knowledge.relationship.Relationship` imported but unused |
| `aegis_os/pipeline/__init__.py` | `26:54` | `F401` | `aegis_os.pipeline.agent_selector_adapter.AgentSelectorAdapter` imported but unused; consider removing, adding to `__all__`, or using a redundant alias |

The protected-base and Integration A blobs are identical:

| Path | Base and Integration A blob |
|---|---|
| `aegis_os/knowledge/knowledge_graph.py` | `61f68fabf9ff2dee871125a9aee8082fbc84a911` |
| `aegis_os/pipeline/__init__.py` | `d4e887bd32c5a3efe2a3e8602afb3c25b13013f8` |

The baseline contains exactly three diagnostics in two files. No other diagnostic is inherited or accepted by this amendment.

## Repository-Wide No-Regression Rule

Repository-wide Ruff output must be compared as a normalized set of:

```text
relative path
line
column
rule code
diagnostic message
```

Absolute working-directory prefixes and output ordering are not significant. All other fields are significant.

The same Ruff version, exact protected-base `pyproject.toml` configuration, command options, and CPython 3.11 environment must be used for both sides of each comparison. The final report must record the Ruff version and exact commands.

A repository-wide result satisfies this amendment only when:

1. The protected base produces exactly the three-diagnostic baseline above.
2. The evaluated integration revision produces exactly the same normalized three-diagnostic set.
3. No diagnostic is added, removed, relocated, recoded, or changed.
4. No authorized integration path has a Ruff violation.

The expected repository-wide Ruff exit code remains nonzero because the inherited baseline is intentionally unremediated. Compliance is determined by exact diagnostic-set equality plus clean scoped checks, not by treating the inherited findings as globally resolved.

## Base Baseline Command

Run the repository-wide baseline command against an exact detached export of protected base `c137005b08c449a8e19f7734098865dd10181955`:

```powershell
python -m ruff check --no-cache --output-format=concise --config pyproject.toml .
```

The export is evidence-only and must not create or move a branch, worktree, or repository reference. Record the complete output, Ruff version, configuration identity, and exit code.

## Stage 1 Scoped Ruff Commands

Run from the preserved Integration A worktree with exact HEAD `fb0364d1b4e0a27953ea7d683a786193d6e61c48`:

```powershell
$stage1Paths = @(
  'aegis_benchmark/runner.py'
  'aegis_os/api/__init__.py'
  'aegis_os/api/app.py'
  'aegis_os/core/cognitive_runtime.py'
  'aegis_os/pipeline/composition.py'
  'tests/api/test_execute_task.py'
  'tests/benchmark/test_runner.py'
  'tests/core/__init__.py'
  'tests/core/test_cognitive_runtime.py'
)

python -m ruff check --no-cache --config pyproject.toml -- $stage1Paths
python -m ruff format --check --no-cache --config pyproject.toml -- $stage1Paths
python -m ruff check --no-cache --output-format=concise --config pyproject.toml .
```

The first two commands must return `PASS`. The repository-wide command must produce the exact inherited baseline and no other diagnostic.

## Amended Stage 1 Gate

Stage 1 satisfies the Ruff gate only when:

1. The complete protected-base Ruff diagnostic set is recorded.
2. Integration A produces the same exact normalized repository-wide diagnostic set.
3. Integration A introduces no new, removed, relocated, recoded, or otherwise changed diagnostic.
4. Direct Ruff lint against all nine Stage 1 paths passes.
5. Ruff format-check against all nine Stage 1 paths passes.

All other Stage 1 gates and accepted evidence remain unchanged:

```text
CPython 3.11.9
create_default_runtime: PASS
Runtime/API smoke: 2 passed
Benchmark delegation: 1 passed
Focused suite: 37 passed
Full repository suite: 125 passed
Dependency integrity: PASS
Changed paths: exactly 9
Unauthorized paths: 0
Worktree: clean
```

## Stage 2 Scoped Ruff Commands

After the amended Stage 1 gate passes and the exact Candidate 2 overlay is committed as Integration B, run:

```powershell
$finalBoundary = @(
  'aegis_benchmark/runner.py'
  'aegis_os/api/__init__.py'
  'aegis_os/api/app.py'
  'aegis_os/api/static/dashboard.js'
  'aegis_os/api/templates/dashboard.html'
  'aegis_os/core/cognitive_runtime.py'
  'aegis_os/execution/conformance.py'
  'aegis_os/execution/execution_engine.py'
  'aegis_os/execution/models.py'
  'aegis_os/pipeline/composition.py'
  'docs/architecture/execution-engine.md'
  'tests/api/test_dashboard.py'
  'tests/api/test_execute_task.py'
  'tests/api/test_execute_task_contract.py'
  'tests/benchmark/test_runner.py'
  'tests/core/__init__.py'
  'tests/core/test_cognitive_runtime.py'
  'tests/execution/test_cancellation.py'
  'tests/execution/test_conformance.py'
  'tests/execution/test_execution_engine.py'
  'tests/execution/test_models.py'
)

python -m ruff check --no-cache --config pyproject.toml -- $finalBoundary
python -m ruff format --check --no-cache --config pyproject.toml -- $finalBoundary
python -m ruff check --no-cache --output-format=concise --config pyproject.toml .
```

The first two commands must return `PASS`. The repository-wide command must produce the exact inherited baseline and no other diagnostic.

## Amended Stage 2 Gate

Stage 2 satisfies the Ruff gate only when:

1. Integration B is created only after the amended Stage 1 gate passes.
2. Direct Ruff lint against the final exact 21-path boundary passes.
3. Ruff format-check against the final exact 21-path boundary passes.
4. Repository-wide Ruff introduces no diagnostic relative to the protected base.
5. No inherited diagnostic is removed, relocated, recoded, or changed.
6. No authorized integration path has a Ruff violation.
7. The repository-wide normalized diagnostic set remains exactly the three-item inherited baseline.

All non-Ruff Stage 2 gates remain unchanged.

## Resumption Authority

Release & Integration is authorized to resume from preserved Integration A commit:

```text
fb0364d1b4e0a27953ea7d683a786193d6e61c48
```

Before resuming, verify that:

- `integration/wo-002-wo-003-c137005b` points exactly to Integration A.
- The Integration A tree remains `b165ad0521d8544f613fd9b1b95e541fd107805a`.
- The integration worktree is clean.
- The recovery tag object and protected target remain unchanged.

If the amended Stage 1 gate passes, Release & Integration may create the already-authorized Integration B as the sole additional commit. Integration B must contain exactly the sixteen Candidate 2 overlay paths and must have Integration A as its sole parent.

The final branch must contain exactly two integration commits after the protected base. No other commit is authorized.

## Prohibited Base Remediation

This amendment does not authorize changes to:

```text
aegis_os/knowledge/knowledge_graph.py
aegis_os/pipeline/__init__.py
```

It also does not authorize changes to Ruff configuration, dependencies, infrastructure, CI, or any other non-allowlisted path. The three inherited diagnostics are recorded as pre-existing technical debt and must remain outside this integration.

Code remediation is not an acceptable substitute for the bounded no-regression evidence.

## Unchanged Controls

All original controls remain effective except the Ruff gates expressly superseded by this amendment. In particular:

- Integration base and source identities remain unchanged.
- Stage 1 remains immutable.
- Integration B remains the only additional authorized commit.
- The final unique boundary remains exactly 21 paths.
- CPython 3.11 remains required.
- Candidate identities and tags must remain unchanged.
- Existing and unrelated work must remain untouched.
- `main` modification, push, publication, release, and WO-004 activation remain unauthorized.
- Post-composition independent QA, Architecture review, governance disposition, and separate promotion authority remain required.

## Required Next Report

The bounded integration composition report must additionally include:

- Exact protected-base and Integration A repository-wide Ruff commands and complete outputs.
- Ruff version and configuration identity.
- Normalized diagnostic-set comparison proving exact equality.
- Stage 1 nine-path lint and format-check commands and results.
- Stage 2 21-path lint and format-check commands and results.
- Final repository-wide diagnostic-set comparison.
- Blob evidence proving both inherited-debt files remain unchanged.
- Confirmation that no base-remediation path was modified.

```text
Amendment status: AUTHORIZED — BOUNDED NO-REGRESSION RUFF BASELINE
Original authorization: 70305cf86c92944149fc337400848b44a0c80309
Integration A preserved: fb0364d1b4e0a27953ea7d683a786193d6e61c48
Inherited Ruff violations: EXACTLY 3 F401 DIAGNOSTICS IN 2 UNCHANGED BASE FILES
Stage 1 scoped lint required: YES — EXACT 9 PATHS MUST PASS
Stage 1 repository no-regression required: YES — EXACT BASELINE EQUALITY
Stage 2 final-boundary lint required: YES — EXACT 21 PATHS MUST PASS
Stage 2 repository no-regression required: YES — EXACT BASELINE EQUALITY
Base remediation authorized: NO
Integration B authorized: YES — SOLE ADDITIONAL COMMIT AFTER AMENDED STAGE 1 PASS
Maximum integration commits: EXACTLY 2
Main modification authorized: NO
Push authorized: NO
Active owner: RELEASE & INTEGRATION ENGINEER
Required next report: AMENDED WO-002/WO-003 BOUNDED INTEGRATION COMPOSITION REPORT
```
