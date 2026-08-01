# Work Order WO-006B: Phase B Simulation Benchmark Corpus

**Status:** ACTIVATION CANDIDATE - IMPLEMENTATION NOT STARTED
**Explicit benchmark authorization:** 2026-08-01
**Authoritative activation base:** 656fce452c9ac9fd287fd86f56dd6c1d476354c1
**Authoritative activation tree:** 8aca9c21817b52a2709858a0989159819a0cdbc5
**Parent runtime work order:** WO-006
**Implementation authority:** docs/specifications/v0.5-phase-b-environment-interaction-layer.md
**Benchmark implementation authority:** GRANTED AS A DISTINCT DECISION; EFFECTIVE ONLY AFTER ACTIVATION-CANDIDATE REVIEW AND PUBLICATION
**Runtime implementation authority:** GOVERNED SEPARATELY BY WO-006
**Integration authority:** NOT GRANTED
**Remote-publication authority:** NOT GRANTED
**Tag and release authority:** NOT GRANTED
**Ruleset-change authority:** NOT GRANTED
**Worktree-cleanup authority:** NOT GRANTED

---

## Objective

Implement the mandatory, separate, simulation-only Phase B benchmark corpus and
evaluator required for acceptance of the WO-006 Environment Interaction Layer,
without changing the legacy benchmark corpus, legacy benchmark behavior,
current cognitive pipeline, current execution engine, dependencies, CI, or
existing reports.

## Separate authorization decision

Benchmark implementation was explicitly authorized on 2026-08-01 as a decision
separate from runtime implementation authorization. This record fixes exact
benchmark paths and validation gates. It does not start implementation and
does not authorize runtime changes.

The authorization becomes operational only after the two-commit governance
activation candidate is independently reviewed, promoted to local main under
separate authority, and published to remote main under separate exact-SHA
authority.

## Legacy benchmark baseline

The repository contains 18 JSON cases across four legacy mission files. Exactly
17 are enabled. The sole disabled record is
`execution-disabled-example`. Therefore the specification's "existing 17
missions" refers to the 17 enabled missions, not the raw JSON object count.

- `benchmarks/missions/analysis.json` - blob `909aa7e1b0e38706fbe4c0e8466f24406d23cde4`; total=5; enabled=5; disabled=0
- `benchmarks/missions/execution.json` - blob `f29c7de9f40bb013ac99c692d301f97cfc3ab1bd`; total=4; enabled=3; disabled=1
- `benchmarks/missions/research.json` - blob `1d9720055a16df95c1ca90a064d1f64e1fa0b29c`; total=6; enabled=6; disabled=0
- `benchmarks/missions/unsupported.json` - blob `5a51038483de93600037c3dd27855b4cd9a516af`; total=3; enabled=3; disabled=0

All four files above must remain byte-for-byte unchanged.

The following existing paths are also preservation-only and may not be modified
under WO-006B:

- `benchmarks/schemas/benchmark-case.schema.json`
- `aegis_benchmark/__init__.py`
- `aegis_benchmark/cli.py`
- `aegis_benchmark/evaluator.py`
- `aegis_benchmark/loader.py`
- `aegis_benchmark/models.py`
- `aegis_benchmark/report.py`
- `aegis_benchmark/runner.py`
- `aegis_benchmark/scoring.py`
- all existing files directly under `tests/benchmark`
- `benchmarks/reports/latest.json`
- `benchmarks/reports/latest.md`

## Exact benchmark implementation allowlist

- `benchmarks/phase_b/environment.json`
- `benchmarks/schemas/environment-benchmark-case.schema.json`
- `aegis_benchmark/environment_models.py`
- `aegis_benchmark/environment_loader.py`
- `aegis_benchmark/environment_evaluator.py`
- `aegis_benchmark/environment_runner.py`
- `aegis_benchmark/environment_report.py`
- `aegis_benchmark/environment_cli.py`
- `tests/benchmark/environment/__init__.py`
- `tests/benchmark/environment/conftest.py`
- `tests/benchmark/environment/test_models.py`
- `tests/benchmark/environment/test_loader.py`
- `tests/benchmark/environment/test_evaluator.py`
- `tests/benchmark/environment/test_runner.py`
- `tests/benchmark/environment/test_report.py`
- `tests/benchmark/environment/test_cli.py`
- `tests/benchmark/environment/test_determinism.py`

Every authorized path is new. No existing benchmark implementation, mission,
schema, test, or report path may be modified.

The new corpus is placed under `benchmarks/phase_b` rather than
`benchmarks/missions` so the existing directory loader continues to discover
exactly the same 17 enabled legacy missions.

## Required Phase B corpus

The new corpus contains exactly 11 deterministic simulation scenarios:

1. successful READ;
2. successful CREATE with idempotency digest;
3. policy denial;
4. approval required;
5. approval granted;
6. unsupported operation or capability;
7. ambiguous environment;
8. no compatible environment;
9. LIVE simulation-only enforcement;
10. malformed adapter normalization;
11. deterministic receipt across repeated runs.

Each case must assert all applicable status, reason, selected environment,
selected adapter, evidence stages, receipt request/result/correlation IDs,
simulation flag, absence of real side effects, and scenario-specific invariants.

## Harness isolation

The Phase B benchmark harness must import and compose the Environment
Interaction Layer directly. It must not call or modify the cognitive pipeline,
current execution engine, API, dashboard, or legacy `BenchmarkRunner`.

The harness may use standard-library file reads only to load the explicit corpus
and standard-library writes only to caller-selected report destinations. The
runtime under benchmark must remain free of filesystem, network, process,
shell, environment, clock, randomness, provider, credential, and machine-state
access.

## Implementation sequencing and worktree

Benchmark implementation is authorized but deferred until an exact runtime
candidate has completed its own pre-freeze validation.

After that candidate exists:

- planned branch: `implementation/wo-006b-environment-benchmarks`;
- planned worktree: `C:\Users\Woolis Shop\Projects\aegis-platform-wo-006b-benchmarks`;
- required starting point: the exact reviewed runtime candidate SHA;
- benchmark commits: local only until independent review;
- automatic merge, push, tag, release, or main modification: prohibited.

## Required validation

1. verify the four legacy mission blob SHAs remain exact;
2. run the unchanged legacy benchmark CLI against `benchmarks/missions` and
   prove exactly 17 enabled cases pass;
3. run the Phase B benchmark CLI against
   `benchmarks/phase_b/environment.json` and prove exactly 11 cases pass;
4. `python -m pytest -q tests/benchmark`;
5. `python -m pytest -q`;
6. Ruff lint and format checks for only the new benchmark modules and tests;
7. `git diff --check`;
8. exact allowlist and commit-range validation;
9. repeated-run byte-equivalence for deterministic Phase B reports;
10. guards proving no runtime external I/O, clock, randomness, provider,
    credential, environment, or machine-state access;
11. proof that the four legacy mission files, existing legacy harness, current
    pipeline, current execution engine, Phase A resources, dependencies, CI,
    governance, and tracked legacy reports remain unchanged.

Generated reports must be written to temporary or operational-evidence
locations and must not modify tracked report files.

## Stop conditions

Stop before implementation if the activation candidate is not independently
accepted and published, no exact runtime candidate exists, a path falls outside
the allowlist, a legacy mission or harness path would change, the 17-enabled
baseline differs, a scenario requires current pipeline or execution-engine
integration, live/provider/external-I/O behavior is proposed, dependency drift
appears, an internal contradiction remains, unrelated worktree changes exist,
or a local or remote protected reference changes without separate authority.

## Current disposition

WO-006B benchmark authority: GRANTED AS A DISTINCT DECISION
Operational effect: PENDING ACTIVATION-CANDIDATE REVIEW AND PUBLICATION
Implementation started: NO
Runtime implementation: GOVERNED SEPARATELY BY WO-006
Integration authority: NOT GRANTED
Remote-publication authority: NOT GRANTED
Tag or release authority: NOT GRANTED
Ruleset-change authority: NOT GRANTED
Worktree-cleanup authority: NOT GRANTED