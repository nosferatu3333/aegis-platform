# Benchmark case format

Benchmark missions are JSON files containing a `cases` array. The runtime
loader is the validation authority for v0.1; the accompanying documentation
schema is at `benchmarks/schemas/benchmark-case.schema.json`.

```json
{
  "suite": "AEGIS Benchmark Suite",
  "version": "0.1",
  "cases": [
    {
      "id": "research-001",
      "title": "Competitor research",
      "category": "research",
      "difficulty": "easy",
      "mission": "Research competitors in the cognitive systems market",
      "expected": {
        "primary_intent": "research",
        "required_capabilities": ["research"],
        "selected_agent": "Research Agent",
        "workflow_step_count": 5,
        "workflow_order_valid": true,
        "analysis_status": "ready"
      },
      "tags": ["research", "market"],
      "enabled": true
    }
  ]
}
```

Required case fields are `id`, `title`, `category`, `difficulty`, `mission`,
and `expected`. `tags` defaults to an empty list and `enabled` defaults to
`true`.

Supported optional expectations are:

- `primary_intent`
- `required_capabilities`
- `selected_agent`
- `workflow_step_count`
- `workflow_order_valid`
- `analysis_status`
- `execution_status`
- `simulated`
- `failure_code`

An omitted expectation is not evaluated and has no effect on the case or suite
score. IDs must be unique across all loaded files. Files and cases are returned
in deterministic ID order, and disabled cases are skipped.
