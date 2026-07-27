# Benchmark suite architecture

## Purpose

`aegis_benchmark` measures how consistently the current AEGIS lifecycle matches
declared expectations. Tests answer whether implementation contracts behave
correctly; benchmarks run representative external missions through those
contracts and score observed capability.

```text
BenchmarkCase
  -> CognitiveRequestPipeline
  -> ExecutionRequest adapter (when expected)
  -> simulated ExecutionEngine (when enabled)
  -> BenchmarkActual
  -> deterministic evaluator
  -> score
  -> JSON and Markdown reports
```

## Components

- `models.py`: case, expectation, actual, criterion, result, and run-summary
  dataclasses.
- `loader.py`: standard-library JSON loading for one file or a directory,
  deterministic ID ordering, runtime validation, disabled-case filtering, and
  duplicate-ID rejection.
- `runner.py`: uses `create_default_pipeline`, `build_execution_request`, and
  `ExecutionEngine`; it does not reproduce pipeline or execution logic.
- `evaluator.py`: exact declared-field comparisons. Required capabilities are
  compared without order sensitivity.
- `scoring.py`: case, suite, category, and metric percentages.
- `report.py`: deterministic JSON and Markdown output.
- `cli.py`: selection, execution mode, output paths, summary, and exit codes.

## Evaluation and scoring

Supported criteria are primary intent, required capabilities, selected agent,
workflow step count, workflow order validity, analysis status, execution
status, simulated flag, and failure code. Omitted expectations do not produce a
criterion or affect a denominator.

Case score is:

```text
passed declared criteria / total declared criteria * 100
```

A case passes only when all evaluated criteria pass. Suite and category scores
aggregate criteria. Named metrics aggregate their mapped criteria. Empty metric
denominators return `0.0`.

## Current suite

The checked-in v0.1 dataset contains 17 enabled cases:

| Category | Cases |
|---|---:|
| research | 6 |
| analysis | 5 |
| unsupported/no-match | 3 |
| simulated execution | 3 |

One future real-tool example is disabled. The checked-in latest report records
17/17 passing and 100% across populated metrics. This demonstrates consistency
against the declared dataset, not general intelligence or real research.

## CLI and reports

```powershell
python -m aegis_benchmark.cli --path benchmarks/missions
```

The CLI supports `--category`, `--case`, `--no-execution`, `--json-output`, and
`--markdown-output`. Default outputs are
`benchmarks/reports/latest.json` and `latest.md`. Exit codes are `0` for all
passing, `1` for benchmark failures, and `2` for loading/selection errors.

## Limitations

- Exact deterministic expectations only; no LLM or semantic judge.
- Small curated dataset aligned to current keyword behavior.
- No historical storage, trends, dashboard, parallelism, or load testing.
- No quality scoring of simulated step output.
- Fixed benchmark clock makes execution receipts repeatable.
- A 100% score can regress when honest edge cases expand coverage.

See the detailed [benchmark guide](../benchmarks/README.md),
[ADR-003](../adr/ADR-003-benchmark-suite.md), and
[v0.4.0 release](../releases/v0.4.0.md).
