# WO-002/WO-003 Bounded Integration Authorization — Python-Only Ruff Target Amendment

**Amendment status:** AUTHORIZED — PYTHON-ONLY STAGE 2 RUFF TARGET
**Date authorized:** 2026-07-30
**Original authorization:** `70305cf86c92944149fc337400848b44a0c80309`
**Ruff baseline amendment:** `b0d6cb5bd93f742ede4c2bd2fcfedb756c2fea58`
**Preserved Integration A:** `fb0364d1b4e0a27953ea7d683a786193d6e61c48`
**Preserved Integration B:** `f727d9f9f2b82b55f79e31008bb79b71477fbc84`
**Integration B tree:** `23f458c2d8a1576c8068aac3de0350dbc792d421`
**Protected base:** `c137005b08c449a8e19f7734098865dd10181955`
**Authorized owner:** Release & Integration Engineer
**Decision owner:** Documentation & Governance
**Policy scope:** Stage 2 Ruff targets for this bounded integration only

---

## Purpose

This amendment corrects the Stage 2 scoped Ruff target. The prior command explicitly passed all 21 authorized boundary paths to Ruff, including JavaScript, HTML, and Markdown files. Ruff 0.15.22 attempted to parse those three non-Python files as Python and emitted 1,278 irrelevant syntax diagnostics.

The result is a governance gate-definition failure, not an implementation defect. Ruff lint and format-check apply to the exact 18 Python paths within the 21-path integration boundary. The three non-Python paths remain fully governed by blob, boundary, test, whitespace, and clean-state controls.

No product, test, architecture-document, configuration, or Infrastructure change is authorized or required.

## Preserved Completed Composition

| Control | Exact identity |
|---|---|
| Integration A | `fb0364d1b4e0a27953ea7d683a786193d6e61c48` |
| Integration B | `f727d9f9f2b82b55f79e31008bb79b71477fbc84` |
| Integration B tree | `23f458c2d8a1576c8068aac3de0350dbc792d421` |
| Integration B parent | `fb0364d1b4e0a27953ea7d683a786193d6e61c48` |
| Final base-to-Integration-B boundary | Exactly 21 paths |
| Unauthorized paths | `0` |
| Integration commits after protected base | Exactly `2` |

Integration A and Integration B are complete and immutable under this authorization. They must not be amended, reset, recreated, replaced, rebuilt, rebased, or supplemented.

## Exact 18-Path Python Manifest

The Stage 2 scoped Ruff target is exactly:

```text
aegis_benchmark/runner.py
aegis_os/api/__init__.py
aegis_os/api/app.py
aegis_os/core/cognitive_runtime.py
aegis_os/execution/conformance.py
aegis_os/execution/execution_engine.py
aegis_os/execution/models.py
aegis_os/pipeline/composition.py
tests/api/test_dashboard.py
tests/api/test_execute_task.py
tests/api/test_execute_task_contract.py
tests/benchmark/test_runner.py
tests/core/__init__.py
tests/core/test_cognitive_runtime.py
tests/execution/test_cancellation.py
tests/execution/test_conformance.py
tests/execution/test_execution_engine.py
tests/execution/test_models.py
```

No Python path may be omitted, added, substituted, or glob-expanded beyond this manifest.

## Exact Three-Path Non-Python Manifest

These paths remain inside the exact 21-path integration boundary but outside Ruff's parser scope:

```text
aegis_os/api/static/dashboard.js
aegis_os/api/templates/dashboard.html
docs/architecture/execution-engine.md
```

Exclusion from the direct Ruff target is not exclusion from integration scope or validation.

## Authorized Python-Only Ruff Commands

Run from the clean integration worktree at exact Integration B:

```powershell
$pythonBoundary = @(
  'aegis_benchmark/runner.py'
  'aegis_os/api/__init__.py'
  'aegis_os/api/app.py'
  'aegis_os/core/cognitive_runtime.py'
  'aegis_os/execution/conformance.py'
  'aegis_os/execution/execution_engine.py'
  'aegis_os/execution/models.py'
  'aegis_os/pipeline/composition.py'
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

python -m ruff check --no-cache --config pyproject.toml -- $pythonBoundary
python -m ruff format --check --no-cache --config pyproject.toml -- $pythonBoundary
```

Both commands must pass. The exact Ruff version and outputs must be recorded in the integration composition report.

## Repository-Wide No-Regression Requirement

The repository-wide command remains:

```powershell
python -m ruff check --no-cache --output-format=concise --config pyproject.toml .
```

Its normalized diagnostic set must remain exactly equal to the protected-base three-diagnostic baseline recorded in the Ruff Baseline Amendment:

1. `aegis_os/knowledge/knowledge_graph.py:1:40` — `F401`.
2. `aegis_os/knowledge/knowledge_graph.py:2:45` — `F401`.
3. `aegis_os/pipeline/__init__.py:26:54` — `F401`.

No diagnostic may be added, removed, relocated, recoded, or changed. No authorized Python integration path may have a Ruff diagnostic. The expected repository-wide Ruff exit code remains nonzero solely because the inherited baseline is intentionally unremediated.

## Non-Python Verification Controls

Each of the three non-Python paths must satisfy:

1. Exact blob equality with WO-003 Candidate 2 commit `eee135547a768c3cad95c1e2e5342e9203620463`.
2. Membership in the exact authorized 21-path boundary.
3. Relevant dashboard and API tests.
4. The complete repository test suite.
5. `git diff --check`.
6. Clean integration worktree after validation.

No change to any non-Python path is authorized or required.

## Accepted Stage 2 Evidence

The following evidence remains accepted against unchanged Integration B:

```text
CPython: 3.11.9
Focused validation: 52 passed
WO-003 validation: 97 passed
Full repository suite: 172 passed
Dependency integrity: PASS
Git whitespace check: PASS
Candidate blobs: exact
Final 21-path boundary: PASS
Unauthorized paths: 0
Worktree: clean
```

The Python-only Ruff commands and repository-wide no-regression comparison remain the corrected gates to be recorded in the final composition report.

## Resumption Authority

Release & Integration is authorized to resume validation from unchanged Integration B:

```text
f727d9f9f2b82b55f79e31008bb79b71477fbc84
```

Before resuming, verify that:

- The integration branch points exactly to Integration B.
- Integration B tree remains `23f458c2d8a1576c8068aac3de0350dbc792d421`.
- Integration B has Integration A as its sole parent.
- The integration worktree is clean.
- Candidate and recovery references remain unchanged.

If all amended validation gates pass, Release & Integration may return the same Integration B SHA as the completed local integration target for independent QA and Architecture review.

No additional integration commit is authorized.

## Unchanged Controls

All prior controls remain effective except the Stage 2 Ruff target expressly corrected here:

- The final integration boundary remains exactly 21 paths.
- All 16 Stage 2 blobs must match Candidate 2.
- The inherited three-diagnostic baseline remains unremediated and unchanged.
- CPython 3.11 remains required.
- Candidate identities and tags remain immutable.
- Governance projection remains unchanged.
- Unrelated documentation and existing work remain untouched.
- Cleanup remains unauthorized.
- `main` modification, push, publication, release, and WO-004 activation remain unauthorized.
- Independent QA and Architecture review of exact Integration B remain required.
- A separate governance disposition and promotion authorization remain required.

## Required Next Report

The amended bounded integration composition report must include:

- Exact 18-path Python manifest.
- Exact three-path non-Python manifest.
- Ruff version and exact Python-only commands.
- Python lint and format-check results.
- Repository-wide normalized no-regression comparison.
- Non-Python Candidate 2 blob proof.
- Relevant dashboard/API, complete-suite, whitespace, and clean-state evidence.
- Confirmation that Integration A and Integration B remain unchanged.
- Confirmation that no additional commit was created.
- Exact Integration B SHA proposed for independent QA and Architecture review.

```text
Amendment status: AUTHORIZED — PYTHON-ONLY STAGE 2 RUFF TARGET
Integration B preserved: f727d9f9f2b82b55f79e31008bb79b71477fbc84
Python Ruff target count: 18
Non-Python boundary count: 3
Python lint required: YES — EXACT 18 PATHS MUST PASS
Python format-check required: YES — EXACT 18 PATHS MUST PASS
Repository no-regression required: YES — EXACT THREE-DIAGNOSTIC BASELINE EQUALITY
Non-Python blob verification required: YES — EXACT CANDIDATE 2 BLOBS
Additional integration commit authorized: NO
Main modification authorized: NO
Push authorized: NO
Active owner: RELEASE & INTEGRATION ENGINEER
Required next report: AMENDED WO-002/WO-003 BOUNDED INTEGRATION COMPOSITION REPORT
```
