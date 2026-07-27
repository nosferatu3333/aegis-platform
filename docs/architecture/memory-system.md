# Memory system status

Memory-related code exists, but it is not part of the FastAPI cognitive
pipeline, simulated execution path, or benchmark lifecycle.

## Implemented

The repository contains small legacy/prototype components:

- `WorkingMemory`: a mutable in-process context list.
- `LongTermMemory`: despite its name, a mutable in-process list.
- `ReflectionMemory`: a mutable in-process reflection list.
- `ExperienceRepository`: a mutable in-process experience list.
- `AgentMemory`: per-agent in-process task/result/score history.
- `StateStore`: direct JSON load/save at a configured path.
- `MemoryManager`: wraps `StateStore` and an in-memory
  `ExperienceRepository`.

The separate legacy `CognitiveOrchestrator` can construct `MemoryManager` and
its learning component can write state. `CognitiveCycle` refers to working,
long-term, and reflection stores, but is not called by the product-facing API.

Request-local pipeline results, execution receipts, API request state, and
benchmark actuals are transient data contracts. They are not a memory system
and are not recalled across requests.

## Conceptual

The code names suggest four possible future roles:

- **Working memory:** bounded active context for one governed run.
- **Episodic memory:** durable, attributable records of executions and
  outcomes.
- **Semantic memory:** validated reusable knowledge with provenance.
- **Reflection memory:** evaluated lessons supported by repeated evidence.

These roles have no unified ownership, lifecycle, schema, retrieval policy, or
integration contract today. Existing class names must not be treated as proof
that those systems are operational.

## Not yet implemented

- Persistent memory in the FastAPI pipeline or execution engine.
- Cross-run recall, retrieval ranking, provenance, or confidence.
- Durable receipt/history database.
- Atomic/versioned state migrations, concurrency control, retention, or
  deletion policy.
- Governance for sensitive data, tenancy, permissions, or audit access.
- Validated reflection promotion and rollback.

Before persistent memory is introduced, AEGIS needs stable execution outcomes,
explicit ownership, safe storage configuration outside the repository,
governance and privacy rules, versioned schemas, provenance, and benchmarks
that prevent single observations from becoming accepted knowledge.

See the [roadmap](../roadmap/ROADMAP.md) and
[Phase 2.5 stabilization notes](../stabilization-phase-2-5.md).
