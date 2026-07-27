# AEGIS proposed roadmap

This roadmap starts from the implemented
[v0.4.0 benchmark-suite baseline](../releases/v0.4.0.md). Future version names,
scope, and ordering are planning proposals, not guarantees.

## Completed

- **v0.1.0:** deterministic backend pipeline and `/analyze-task`.
- **v0.2.0:** dashboard for mission analysis.
- **v0.3.0:** governed simulated execution contracts and receipts.
- **v0.4.0:** deterministic external benchmark suite.

See [release history](../releases/RELEASE_HISTORY.md) and the compact
[milestone matrix](MILESTONES.md).

## Next — v0.5.0 Environment Interaction Layer — Simulation First

- **Objective:** establish the governed boundary through which all future
  external domains are requested, authorized, resolved, invoked, and audited.
- **Phase A — Operational Resource Model:** provider-neutral identities, types,
  references, descriptors, requirements, relations, synthetic in-memory
  catalog, deterministic resolution outcomes, and provenance contracts.
- **Phase B — Environment Interaction Layer:** environment/capability/request/
  result/error contracts; deterministic registry; policy-decision and
  approval-requirement interfaces; one deterministic simulation adapter;
  interaction receipts and execution correlation; stable failure taxonomy.
- **Exclusions:** real filesystem, network, HTTP, shell/process, Git, database,
  email, calendar, queue, MCP, plugin, human-action, or external-agent
  integration; secrets; background work; autonomous actions; production
  sandboxing.
- **Dependencies:** stable v0.3 execution contracts, v0.4 benchmark harness,
  request correlation, explicit risk mapping,
  [ADR-002](../adr/ADR-002-governed-execution.md), and proposed
  [ADR-004](../adr/ADR-004-environment-interface.md) and
  [ADR-005](../adr/ADR-005-operational-resource-model.md).
- **Completion evidence:** deterministic contract/registry/receipt tests;
  resource identity/reference/requirement/resolution tests; policy-bypass
  prevention; allow, deny, restrict, approval-required, ambiguous/unavailable,
  missing-adapter, timeout/cancellation, correlation, provenance, and
  simulation-only cases; no external action.
- **Benchmark implications:** add optional resource inference/type/resolution,
  environment, capability, permission, policy, approval, adapter-resolution,
  provenance, error, receipt-completeness, transition, and simulation criteria
  without grading external content quality.

## Planned — v0.6.0 Persistent Memory

- **Objective:** introduce governed, versioned cross-run storage for defined
  memory roles.
- **Minimum scope:** ownership model; external runtime storage location;
  episodic receipt records; provenance; bounded working context; schema
  versioning; atomic writes; retention and deletion.
- **Exclusions:** unvalidated self-learning, implicit memory writes, global user
  profiling, vector-database dependency by default, and treating existing
  in-memory prototypes as production-ready.
- **Dependencies:** stable outcomes and audit identity from v0.5, privacy and
  authorization policy, migration/rollback design.
- **Completion evidence:** restart persistence, corruption recovery, migration,
  isolation, access-control, retention, and provenance tests.
- **Benchmark implications:** repeatable recall/forgetting cases, cross-run
  isolation, and provenance accuracy; no subjective memory-quality score.

## Planned — v0.7.0 Reflection and Learning

- **Objective:** derive candidate lessons from measured outcomes and promote
  them only with explicit evidence.
- **Minimum scope:** reflection contract; evidence references; repeated-run
  validation; promotion/rejection states; versioning; rollback; human review
  boundary for consequential changes.
- **Exclusions:** one-shot self-modification, opaque LLM judging, autonomous
  prompt/code rewriting, and unsourced semantic-memory updates.
- **Dependencies:** durable outcomes and provenance from v0.6, measurable task
  criteria, governance over writes and promotions.
- **Completion evidence:** tests for insufficient, repeated, conflicting, and
  revoked evidence; deterministic promotion policy.
- **Benchmark implications:** longitudinal evidence fixtures and promotion
  correctness, while reflection quality remains unscored until an objective
  rubric exists.

## Planned — v0.8.0 Multi-Agent Collaboration

- **Objective:** coordinate multiple bounded agent roles through one governed
  workflow.
- **Minimum scope:** typed delegation plan; role/capability constraints;
  deterministic dependency order; shared-context boundaries; per-agent
  receipts; aggregate failure semantics.
- **Exclusions:** unconstrained agent spawning, parallelism as a default,
  recursive autonomous teams, and leaderboard/ranking claims.
- **Dependencies:** environment-interaction policy, persistent scoped context,
  auditable outcomes, and cancellation/budget controls.
- **Completion evidence:** delegation, dependency, partial-failure, context
  isolation, budget, and aggregate-receipt tests.
- **Benchmark implications:** collaboration cases for correct role selection,
  ordering, containment, and failure propagation; performance load testing
  remains separate.

## Planned — v0.9.0 Governance and Policy Engine

- **Objective:** make risk, permissions, approvals, budgets, and audit policy
  first-class enforceable decisions across cognition and execution.
- **Minimum scope:** versioned policy model; request/identity context;
  risk-to-decision rules; human approval records; least privilege; policy
  evaluation traces; tamper-aware audit export.
- **Exclusions:** regulatory certification claims, universal policy language,
  authentication provider implementation, and automatic high-risk approval.
- **Dependencies:** every earlier action and memory write exposes typed scopes
  and stable audit events.
- **Completion evidence:** policy matrices, deny-by-default tests, bypass
  prevention, approval expiry/revocation, version replay, and audit integrity.
- **Benchmark implications:** governance scenario suite separated by policy
  version, with explicit weighted scoring deferred until weights have an
  approved rationale.

## Exploratory — v1.0.0 Cognitive Operating System MVP

- **Objective:** integrate the proven pipeline, governed environment
  interactions, memory, evidence-based reflection, collaboration, and policy
  into one supportable product boundary.
- **Minimum scope:** documented composition; stable public contracts; migration
  path; operational observability; failure recovery; security review; complete
  user-visible simulation/real-action distinctions.
- **Exclusions:** claims of general intelligence, unrestricted autonomy,
  unsupported external systems, and production readiness without deployment
  and security evidence.
- **Dependencies:** completion and integration evidence from v0.5–v0.9 plus
  ownership decisions for legacy Platform/Core-style components.
- **Completion evidence:** clean installation, contract compatibility, end-to-
  end governed scenarios, security and recovery tests, documentation, and a
  release-specific benchmark baseline.
- **Benchmark implications:** broaden curated capability and governance cases;
  add regression history only after a durable results model is approved.

## Roadmap boundaries

Historical database storage, benchmark dashboards, semantic/LLM judging,
leaderboards, large-scale load suites, external APIs, and CI publishing are not
implicitly authorized by this roadmap. Each requires a separate decision,
threat model, ownership, and completion evidence.
