# ADR-004 — Governed Environment Interaction Layer

- **Status:** Proposed

## Context

AEGIS v0.4.0 has a deterministic cognitive pipeline, simulated execution
engine, request-local receipts, and benchmark suite. It has no external tool or
provider integration, and its `permissions` field is descriptive rather than
enforced.

Future filesystem, web, Git, database, email, calendar, process, MCP, human, or
agent interactions share a need for stable validation, policy, approvals,
adapter discovery, normalized outcomes, failure isolation, and audit
correlation. Allowing each subsystem or agent to invent this boundary would
couple cognition to providers and create authorization bypass paths.

## Decision

AEGIS will introduce a governed, adapter-driven **Environment Interaction
Layer** between execution orchestration and external systems.

Execution will submit normalized `EnvironmentRequest` contracts to this layer.
The layer will own validation, policy and approval interception, deterministic
registry resolution, controlled adapter invocation, result/error
normalization, and `InteractionReceipt` creation. The cognitive pipeline and
execution engine will not invoke concrete adapters directly.

The first implementation milestone will be simulation-only and perform no
external action.

## Rationale

“Environment” models the trust and policy boundary around an external domain;
it is broader and more stable than a registry of callable functions. The
abstraction supports provider independence, least privilege, consistent
failures, complete receipts, simulation, and future benchmark coverage without
placing provider SDKs in the kernel.

## Consequences

- External capabilities gain one mandatory interception path.
- Provider implementations remain replaceable behind normalized contracts.
- Policy, approval, registry, result, error, and receipt contracts must be
  designed before real adapters.
- The layer introduces additional states and identities that execution receipts
  must reference.
- A common abstraction cannot erase environment-specific security policies;
  those remain explicit configuration and adapter responsibilities.
- No real capability is delivered merely by accepting this ADR.

## Alternatives considered

- **Direct tool calls from agents:** rejected because agents could bypass
  validation, policy, approval, and audit correlation.
- **Provider-specific integrations inside the execution engine:** rejected
  because orchestration would depend on SDKs, credentials, and provider error
  behavior.
- **A narrow tool registry without an environment abstraction:** rejected
  because operation discovery alone does not model domain identity, trust,
  permission scopes, availability, provider selection, or normalized receipts.
- **Postpone the abstraction until real integrations exist:** rejected because
  the first real adapter would otherwise establish unsafe accidental contracts;
  architecture and deterministic simulation can validate the boundary first.

## Current limitations

The environment contracts, registry, policy decisions, approvals, adapter
interface, invocation controller, stable environment errors, and interaction
receipts do not exist in runtime code. Current execution remains entirely
simulated and request-local.

## Security implications

The proposed layer must default deny, enforce least privilege and read-only
modes, isolate secrets, minimize/redact audit data, treat provider output as
untrusted, prevent prompt-injection content from changing authority, and
eventually isolate network/filesystem/process adapters. Adapter registration
must never imply authorization. Simulation-only enforcement must be testable
before any external integration.

## Related modules and documents

- Current `aegis_os.execution` contracts and engine
- Empty current `aegis_os.governance` package
- [Environment Interaction Layer architecture](../architecture/environment-interface.md)
- [Governance status](../architecture/governance.md)
- [Execution architecture](../architecture/execution-engine.md)
- [Roadmap](../roadmap/ROADMAP.md)
- [ADR-002](ADR-002-governed-execution.md)

## Relationship to proposed v0.5.0

Proposed v0.5.0 is **Environment Interaction Layer — Simulation First**. It
should implement only normalized contracts, deterministic registry and policy
interfaces, a simulation adapter, stable results/errors, receipts, tests,
benchmarks, and documentation. Real filesystem, network, provider, process,
email, calendar, Git, database, MCP, plugin, memory, secret, or autonomous
capabilities remain excluded.
