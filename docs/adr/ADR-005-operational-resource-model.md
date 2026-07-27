# ADR-005 — Provider-neutral Operational Resource Model

- **Status:** Proposed

## Context

The v0.4.0 runtime represents missions, selected capabilities, workflows,
execution steps/receipts, and benchmark cases, but it has no shared model for
the entities those workflows may require or target. The proposed Environment
Interaction Layer defines a governed external boundary, yet an environment is
not the semantic resource being accessed.

Without a resource model, future workflows could embed provider paths, URIs,
adapter names, or arbitrary payloads. That would couple cognition to providers,
obscure ownership and permission scope, and make resolution, provenance,
observations, receipts, and memory integration inconsistent.

## Decision

AEGIS will represent external and internal operational entities through a
provider-neutral **Operational Resource Model** before selecting environments
or adapters.

Missions and workflows will express `ResourceRequirement` values. A future
resolver will produce auditable `ResourceResolution` values containing
lightweight `ResourceReference` targets. Environment requests will use resolved
references where applicable. Resource identity remains distinct from location,
environment, adapter, operation, result, artifact, observation, memory, and
knowledge.

The model will remain semantic. It will not invoke operations, register
providers, or replace execution, governance, environment registries, memory, or
knowledge systems.

## Rationale

Resource-first reasoning preserves mission meaning across provider/location
changes, enables deterministic prerequisite resolution, exposes ambiguity and
unavailability before invocation, gives governance a precise target/scope, and
supports provider-neutral observations and receipts.

The intended statement is “resource X, capability Y, permission Z,” not merely
“tool T.”

## Consequences

- A stable identity/reference/type vocabulary must precede real integrations.
- Workflow and environment contracts gain explicit resource correlations.
- Resource catalogs and environment registries remain separate responsibilities.
- Provider-specific locations become replaceable metadata rather than workflow
  identity.
- Governance must apply to resolution as well as invocation.
- Type taxonomy and relations require disciplined extensibility without
  becoming a premature knowledge graph.
- No operational capability is delivered by accepting this ADR.

## Alternatives considered

- **Direct tool selection:** rejected because it collapses semantic need,
  provider choice, permission, and action.
- **Adapter-specific targets:** rejected because workflows would depend on
  providers and adapter versions.
- **Raw URI/path references in workflows:** rejected because identity,
  authority, classification, version, and policy scope become ambiguous.
- **Treat every resource as an environment definition:** rejected because a
  semantic target and its access/trust domain have different identity,
  lifecycle, and ownership.
- **Postpone the model until real integrations exist:** rejected because the
  first adapter would establish accidental provider-coupled contracts.
- **Adopt a full knowledge graph immediately:** rejected as excessive before
  stable identity, references, requirements, deterministic resolution, and
  governance exist.

## Current limitations

No resource contracts, catalog, type registry, discovery, resolver,
observations, persistence, or workflow integration exist in runtime code.
Current capability IDs identify agent/profile matching, not operational
resources. Existing file paths and benchmark report paths are implementation
locations, not `ResourceReference` contracts.

## Security implications

The model must default deny access, separate ownership from access authority,
scope permissions to resource/capability/environment, isolate tenants, classify
sensitive/untrusted resources, exclude credentials and secrets, preserve
provenance, minimize/redact receipts, and support revocation/deletion semantics.
Resource relations must not imply transitive authorization or trust.

## Relationship to Environment Interaction Layer

The resource model provides the semantic target and resolved reference. The
Environment Interaction Layer provides validation, policy/approval
interception, environment/adapter resolution, controlled invocation,
normalized results, and receipts. An environment may expose many resources and
one resource may have multiple environment locations.

See [ADR-004](ADR-004-environment-interface.md) and the
[environment architecture](../architecture/environment-interface.md).

## Relationship to future memory and knowledge

Resources are operational entities. Observations are resource-linked claims.
Memory may later retain experiences/observations; knowledge may later contain
verified claims. Neither system should use the resource catalog as a substitute
for evidence, provenance, or promotion policy.

## Relationship to proposed v0.5

The Operational Resource Model is proposed as **v0.5 Phase A**, followed by
**Phase B: Environment Interaction Layer — Simulation First**. Phase A should
remain in-memory, synthetic, deterministic, and non-operational. It must not add
resource discovery, persistence, provider integration, or external action.

## Related modules and documents

- Current `aegis_os.pipeline.models`
- Current `aegis_os.execution.models`
- Current `aegis_benchmark.models`
- [Operational Resource Model](../architecture/operational-resource-model.md)
- [Governance status](../architecture/governance.md)
- [Memory status](../architecture/memory-system.md)
- [Roadmap](../roadmap/ROADMAP.md)
