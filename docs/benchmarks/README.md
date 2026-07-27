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

## Run

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

See [benchmark-case-format.md](benchmark-case-format.md) for data contracts and
[scoring-model.md](scoring-model.md) for deterministic scoring.
