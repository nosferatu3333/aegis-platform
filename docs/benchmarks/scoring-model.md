# Deterministic scoring model

Every declared expectation produces one `CriterionResult` containing the
criterion name, expected value, actual value, and pass/fail outcome. Values use
exact deterministic comparison; required capabilities are compared as
order-independent sets represented by lists.

No LLM judge, semantic similarity, weighted governance score, or subjective
review is used.

## Case score

```text
passed declared criteria / total declared criteria * 100
```

A case passes only when every evaluated criterion passes. Omitted expectations
do not enter the denominator. With `--no-execution`, execution-status and
simulation criteria are excluded because execution was intentionally not run.

## Suite score and metrics

Overall score applies the same formula across all evaluated criteria in the
suite. The summary also reports:

- intent accuracy
- capability accuracy
- agent-selection accuracy
- workflow accuracy, combining count and order criteria
- analysis-status accuracy
- execution accuracy
- simulation-compliance accuracy

Each metric is `passed / evaluated * 100`. A metric with no evaluated criteria
returns `0.0`, avoiding division by zero. Category scores use all evaluated
criteria within that category.
