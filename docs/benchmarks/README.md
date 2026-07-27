# AEGIS Benchmark Suite v0.1

The benchmark suite measures the consistency of the current AEGIS cognitive
lifecycle. It is distinct from unit tests: tests verify implementation
correctness, while benchmark cases compare declared mission expectations with
outputs from the real pipeline and simulated execution engine.

```text
BenchmarkCase
-> CognitiveRequestPipeline
-> ExecutionRequest adapter (when requested)
-> simulated ExecutionEngine (when requested)
-> BenchmarkActual
-> deterministic evaluator
-> score
-> JSON and Markdown reports
```

The suite does not duplicate intent analysis, capability matching, agent
selection, workflow generation, or execution logic. It performs no internet
research, external API calls, real tool actions, LLM grading, or semantic
similarity evaluation.

## Quick start

```powershell
python -m aegis_benchmark.cli --path benchmarks/missions
```

Useful filters and outputs:

```powershell
python -m aegis_benchmark.cli `
  --path benchmarks/missions `
  --category research

python -m aegis_benchmark.cli `
  --path benchmarks/missions `
  --case execution-001 `
  --json-output benchmarks/reports/custom.json `
  --markdown-output benchmarks/reports/custom.md

python -m aegis_benchmark.cli `
  --path benchmarks/missions `
  --no-execution
```

The default reports are `benchmarks/reports/latest.json` and
`benchmarks/reports/latest.md`. Disabled cases are skipped. Exit code `0`
means every selected enabled case passed; `1` means at least one failed, and
`2` indicates loading or selection failure.

## Directory structure

```text
aegis_benchmark/           Python contracts, loader, runner, evaluator, reports
benchmarks/missions/       External JSON case files
benchmarks/schemas/        Documentation JSON Schema
benchmarks/reports/        Generated latest.json and latest.md
tests/benchmark/           Contract and integration tests
docs/benchmarks/           Maintainer documentation
```

## Add cases

Add a uniquely identified object to a JSON file under `benchmarks/missions`.
Declare only expectations supported by the current runtime and only fields the
case intends to score. Run the loader/tests and full CLI before accepting a
case. Disabled future examples may use `"enabled": false`; they are not loaded
or scored.

See [benchmark-case-format.md](benchmark-case-format.md) for the exact
contracts and the documentation schema. The Python loader remains runtime
validation authority.

## Generated reports

The JSON report includes summary metrics, category breakdown, every result,
criteria, actual analysis, and any simulated receipt. The Markdown report is a
concise review surface. Reports contain a fixed injected benchmark timestamp in
simulated receipts, so repeated runs remain deterministic.

The checked-in [latest Markdown report](../../benchmarks/reports/latest.md)
records 17/17 enabled cases passing. A perfect score applies only to those
declared expectations.

## Limitations

- Six research, five analysis, three unsupported, and three simulated-execution
  cases; one future example is disabled.
- Exact comparisons only; no semantic or output-quality judge.
- No trends, database, dashboard, parallelism, load testing, or leaderboard.
- Research cases test classification and lifecycle consistency, not internet
  research.

See [scoring-model.md](scoring-model.md),
[benchmark architecture](../architecture/benchmark-suite.md), and
[ADR-003](../adr/ADR-003-benchmark-suite.md).
