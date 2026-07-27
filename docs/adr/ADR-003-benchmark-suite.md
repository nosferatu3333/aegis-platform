# ADR-003 — External deterministic benchmarks separate from tests

- **Status:** Accepted
- **Date:** 2026-07-26

## Context

By v0.3.0, tests verified contracts and transitions but did not provide a
capability-oriented view across representative missions. Benchmark cases also
needed to evolve without duplicating or embedding expectations in production
logic.

## Decision

Create a separate `aegis_benchmark` package. Store mission cases in external
JSON, run them through the real pipeline/adapter/engine, compare only declared
expectations deterministically, and generate JSON/Markdown reports. Keep
runtime validation in the loader and provide a documentation JSON Schema.

## Consequences

- Tests answer implementation correctness; benchmarks report consistency on a
  declared dataset.
- Omitted expectations do not dilute scores.
- Cases are reviewable and extensible without changing Python algorithms.
- Scores are limited by dataset scope and exact criteria.

## Alternatives considered

- Treat pytest counts as capability scores: rejected because passing contract
  tests do not measure representative mission behavior.
- LLM or semantic judging: deferred because it adds nondeterminism, cost,
  external dependencies, and rubric ambiguity.
- Embed cases in Python: rejected in favor of external reviewable data.
- Add a database/dashboard: deferred until a justified history model exists.

## Current limitations

Seventeen enabled cases, exact matching, no output-quality/reflection scoring,
history, parallel execution, load testing, or public leaderboard.

## Related modules and releases

`aegis_benchmark.*`, `benchmarks/missions`,
[benchmark architecture](../architecture/benchmark-suite.md),
[benchmark guide](../benchmarks/README.md), and
[v0.4.0](../releases/v0.4.0.md).
