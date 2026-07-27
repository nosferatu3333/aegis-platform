# Cognitive pipeline

## Scope

The implemented product-facing lifecycle is a deterministic, synchronous
request pipeline:

```text
Mission
  -> Intent Analysis
  -> Required Capabilities
  -> Agent Selection
  -> Workflow Generation
  -> CognitiveRequestResult
```

This path powers `POST /analyze-task`, precedes `POST /execute-task`, and is
reused by the [benchmark suite](benchmark-suite.md). It is separate from the
legacy `aegis_os.cognition.CognitiveOrchestrator` simulation.

## Composition and modules

`aegis_os.pipeline.composition.create_default_pipeline()` is the shared
composition root. It registers two `AgentProfile` objects:

- **Research Agent:** `research`, `knowledge`
- **Analysis Agent:** `analysis`, `evaluation`

It connects `AgentRegistry` and `CapabilityMatcher` through
`AgentSelectorAdapter`, then constructs `CognitiveRequestPipeline`.

The processing modules are:

- `pipeline.intent_analyzer`: token normalization, keyword classification,
  complexity, risk, and planning/execution flags.
- `pipeline.agent_selector_adapter`: normalizes required capability names and
  delegates exact matching.
- `agents.capability_matcher`: selects the first highest-scoring profile with
  at least one match.
- `pipeline.workflow_generator`: converts a profile workflow when available or
  supplies the five-step default workflow.
- `pipeline.models`: serializable pipeline contracts.

## Data contracts

`IntentAnalysis` records primary and secondary intents, required capabilities,
detected concepts, complexity, risk, and planning/execution flags.
`CapabilityMatch` records the selected ID/name and matching evidence.
`WorkflowStep` records order, title, description, capability ID, and status.
`CognitiveRequestResult` combines these fields with task, workflow, status,
metadata, and schema version.

The response schema version is `1.0`. Pipeline metadata currently reports
pipeline version `0.1.0`; this is not the package or milestone version.

## Ready and failed outcomes

A matching profile yields `PipelineStatus.READY` and an ordered workflow.
No matching profile yields `PipelineStatus.FAILED`, capability ID/name
`unknown`, an empty workflow, and:

```json
{
  "failure_code": "no_capability_match",
  "failure_reason": "No registered profile matched the required capabilities."
}
```

Blank tasks raise `ValueError` in the pipeline and are returned as HTTP `422`
by the API.

## API correlation

The API accepts a valid caller `X-Request-ID` or generates a UUID. The ID is
stored on request-local FastAPI state, returned in the response header and JSON
body, and included in structured log messages. Correlation is an API concern;
`CognitiveRequestResult` itself has no request-ID field.

## Supported classification

The analyzer recognizes keyword groups for `planning`, `research`, `analysis`,
`development`, `execution`, and `communication`; unmatched text becomes
`general_reasoning`. Only these mappings produce required capabilities:

| Intent | Required capability |
|---|---|
| research | `research` |
| analysis | `analysis` |
| development | `execution` |
| execution | `execution` |

Because the default registry has no execution profile, development/execution
missions normally produce a no-match result. Planning, communication, and
general reasoning also have no mapped selectable profile.

## Limitations

- Classification is exact, rule-based token matching, not adaptive reasoning.
- There is no semantic similarity, negation handling, model inference, or
  confidence learned from data.
- Agent matching is exact capability overlap and registration-order-sensitive
  on ties.
- Risk classification is descriptive; it does not enforce policy.
- Generated workflows are generic five-step plans, not evidence of real work.
- The pipeline is synchronous and request-local.

See [ADR-001](../adr/ADR-001-cognitive-pipeline.md), the
[execution layer](execution-engine.md), and the
[v0.1.0 release](../releases/v0.1.0.md).
