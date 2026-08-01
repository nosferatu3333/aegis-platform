$ErrorActionPreference = "Stop"

if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$repo = "$env:USERPROFILE\Projects\aegis-platform"
$worktree = "$env:USERPROFILE\Projects\aegis-platform-wo-005-candidate"
$branch = "documentation/wo-005-environment-interaction-candidate"

$base = "be7502f73b51808d54728f912ead46ad0073c7b9"
$authorizationMain = "7a34c38d6210a2ed58f8966b3143ab67103424e4"
$reviewWorktree = "$env:USERPROFILE\Projects\aegis-platform-wo-005-review"
$reviewBranch = "governance/wo-005-candidate-review"
$designationSubject = "Designate WO-005 candidate for review"
$traceabilityRelative = "governance/TRACEABILITY.md"
$workOrderRelative = "governance/work-orders/WO-005_ENVIRONMENT_INTERACTION_LAYER_SPECIFICATION.md"
$governancePaths = @($traceabilityRelative, $workOrderRelative)
$operationsRoot = [Environment]::GetEnvironmentVariable("AEGIS_OPERATIONS", "User")
if ([string]::IsNullOrWhiteSpace($operationsRoot)) {
    $operationsRoot = "$env:USERPROFILE\Projects\AEGIS-operations"
}
$logDirectory = Join-Path $operationsRoot "logs\WO-005"
$manifestPath = Join-Path $logDirectory "WO-005-candidate-designation.txt"
$commitSubject = "Define WO-005 environment interaction specification"

$adrRelative = "docs/adr/ADR-006-environment-interaction-layer.md"
$architectureRelative = "docs/architecture/environment-interaction-layer.md"
$specRelative = "docs/specifications/v0.5-phase-b-environment-interaction-layer.md"
$roadmapRelative = "docs/roadmap/ROADMAP.md"

$expectedPaths = @(
    $adrRelative,
    $architectureRelative,
    $specRelative,
    $roadmapRelative
)

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Invoke-Native {
    param(
        [scriptblock]$Command,
        [string]$Label,
        [switch]$AllowExitOne
    )

    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    try {
        & $Command
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedPreference
    }

    if ($exitCode -ne 0 -and -not ($AllowExitOne -and $exitCode -eq 1)) {
        throw "$Label failed with exit code $exitCode."
    }

    return $exitCode
}

function Get-LiveRemoteMain {
    param([string]$Repository)

    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    try {
        $lines = @(
            & git -C $Repository ls-remote --heads origin refs/heads/main
        )
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedPreference
    }

    if ($exitCode -ne 0) {
        throw "Unable to read live remote main."
    }

    if ($lines.Count -ne 1) {
        throw "Expected exactly one live remote main reference."
    }

    return (($lines[0] -split "\s+")[0]).Trim()
}

function Assert-ExactPathSet {
    param(
        [string[]]$Actual,
        [string[]]$Expected,
        [string]$Label
    )

    $unexpected = @($Actual | Where-Object { $_ -notin $Expected })
    $missing = @($Expected | Where-Object { $_ -notin $Actual })

    if (
        $Actual.Count -ne $Expected.Count -or
        $unexpected.Count -gt 0 -or
        $missing.Count -gt 0
    ) {
        Write-Host "$Label actual paths:"
        $Actual | ForEach-Object { Write-Host " - $_" }
        throw "$Label path boundary mismatch."
    }
}

function Assert-AllWorktreesClean {
    param([string]$Repository)

    $paths = @(
        git -C $Repository worktree list --porcelain |
            Where-Object { $_ -like "worktree *" } |
            ForEach-Object { $_.Substring(9) }
    )

    foreach ($path in $paths) {
        if (-not (Test-Path -LiteralPath $path)) {
            throw "Registered worktree path is unavailable: $path"
        }

        if (@(git -C $path status --short).Count -ne 0) {
            throw "Registered worktree is not clean: $path"
        }
    }
}

function Replace-ExactlyOnce {
    param(
        [string]$Text,
        [string]$OldValue,
        [string]$NewValue,
        [string]$Label
    )

    $first = $Text.IndexOf($OldValue, [System.StringComparison]::Ordinal)

    if ($first -lt 0) {
        throw "Required text was not found for $Label."
    }

    $second = $Text.IndexOf(
        $OldValue,
        $first + $OldValue.Length,
        [System.StringComparison]::Ordinal
    )

    if ($second -ge 0) {
        throw "Required text occurs more than once for $Label."
    }

    return $Text.Substring(0, $first) +
        $NewValue +
        $Text.Substring($first + $OldValue.Length)
}

Write-Host "`n=== WO-005 DELIVERABLE PREFLIGHT ==="

if (-not (Test-Path -LiteralPath $repo)) {
    throw "Repository not found: $repo"
}

Invoke-Native {
    git -C $repo fetch origin `
        "+refs/heads/main:refs/remotes/origin/main"
} "Remote main refresh"

$originMain = (
    git -C $repo rev-parse refs/remotes/origin/main
).Trim()

$liveMain = Get-LiveRemoteMain $repo
$localMain = (git -C $repo rev-parse refs/heads/main).Trim()

if ($originMain -ne $authorizationMain) {
    throw "origin/main does not match the published WO-005 authorization commit."
}

if ($liveMain -ne $authorizationMain) {
    throw "Live remote main does not match the published WO-005 authorization commit."
}

if ($localMain -ne $authorizationMain) {
    throw "Local main does not match the published WO-005 authorization commit."
}

Assert-AllWorktreesClean $repo

if (Test-Path -LiteralPath $worktree) {
    throw "WO-005 deliverable worktree already exists: $worktree"
}

if (@(git -C $repo branch --list $branch).Count -ne 0) {
    throw "WO-005 deliverable branch already exists: $branch"
}

foreach ($path in @(
    $adrRelative,
    $architectureRelative,
    $roadmapRelative
)) {
    git -C $repo cat-file -e "${base}:$path"

    if ($LASTEXITCODE -ne 0) {
        throw "Required source document is missing: $path"
    }
}

$existingSpec = @(
    git -C $repo ls-tree -r --name-only $base -- $specRelative
)

if ($LASTEXITCODE -ne 0) {
    throw "Unable to inspect the Phase B specification path."
}

if ($existingSpec.Count -ne 0) {
    throw "The Phase B specification already exists on the authorized base."
}

Write-Host "Authorized base, remote identity, clean state, and paths: PASS"

Write-Host "`n=== CREATE WO-005 DELIVERABLE WORKTREE ==="

Invoke-Native {
    git -C $repo worktree add `
        -b $branch `
        $worktree `
        $base
} "WO-005 deliverable worktree creation"

$adrPath = Join-Path $worktree $adrRelative
$architecturePath = Join-Path $worktree $architectureRelative
$specPath = Join-Path $worktree $specRelative
$roadmapPath = Join-Path $worktree $roadmapRelative

try {
    Write-Host "`n=== ACCEPT ADR-006 ==="

    $adr = [System.IO.File]::ReadAllText($adrPath)
    $adr = $adr -replace "`r`n", "`n"

    if ($adr.Contains("## WO-005 acceptance record")) {
        throw "ADR-006 already contains a WO-005 acceptance record."
    }

    $adr = Replace-ExactlyOnce `
        -Text $adr `
        -OldValue "- **Status:** Proposed" `
        -NewValue "- **Status:** Accepted" `
        -Label "ADR-006 status"

    $adrAcceptance = @'

## WO-005 acceptance record

- Acceptance date: 2026-07-31
- Governing work order: `WO-005`
- Authoritative base: `be7502f73b51808d54728f912ead46ad0073c7b9`
- Decision scope: provider-neutral, deterministic, simulation-first Phase B
- Runtime implementation: not included
- Live providers, credentials, persistence, and external I/O: not authorized

The exact implementation contracts, module boundary, failure taxonomy, and
validation obligations are defined by
[`v0.5 Phase B — Environment Interaction Layer specification`](../specifications/v0.5-phase-b-environment-interaction-layer.md).

Acceptance of this decision does not authorize implementation, integration,
publication of a deliverable candidate, live execution, or provider access.
Each remains subject to separate governance authority.
'@

    [System.IO.File]::WriteAllText(
        $adrPath,
        $adr.TrimEnd() + $adrAcceptance + "`n",
        $utf8NoBom
    )

    Write-Host "ADR-006 decision state: ACCEPTED IN DELIVERABLE"

    Write-Host "`n=== RECONCILE PHASE B ARCHITECTURE ==="

    $architecture = [System.IO.File]::ReadAllText($architecturePath)
    $architecture = $architecture -replace "`r`n", "`n"

    if ($architecture.Contains("## 30. WO-005 specification handoff")) {
        throw "The architecture already contains the WO-005 handoff."
    }

    $architecture = Replace-ExactlyOnce `
        -Text $architecture `
        -OldValue "> **Status: Proposed architecture.**" `
        -NewValue "> **Status: Accepted architecture; runtime not implemented.**" `
        -Label "architecture status"

    $architectureHandoff = @'

## 30. WO-005 specification handoff

WO-005 accepts this architecture and resolves its implementation-open decisions
in the normative
[Phase B implementation specification](../specifications/v0.5-phase-b-environment-interaction-layer.md).

The accepted first runtime increment is bounded to:

- immutable provider-neutral contracts;
- an explicit instance-owned registry;
- deterministic environment resolution;
- a deterministic simulation-only policy evaluator;
- an explicit approval boundary;
- deterministic simulated adapters;
- one lifecycle service;
- immutable interaction receipts;
- focused tests with no external I/O.

The specification fixes `simulated` as an orthogonal boolean rather than a
result status, retains `LIST` as distinct from `SEARCH`, uses schema version
`1.0`, and defines exact error and policy enums.

The first runtime increment remains separate from the cognitive pipeline,
execution engine, API, dashboard, benchmark fixtures, persistent approvals,
observations, memory, learning, credentials, live providers, and all external
side effects.

The future implementation path allowlist is authoritative only when a later
work order explicitly activates it. This accepted architecture and
specification do not themselves authorize code changes.
'@

    [System.IO.File]::WriteAllText(
        $architecturePath,
        $architecture.TrimEnd() + $architectureHandoff + "`n",
        $utf8NoBom
    )

    Write-Host "Architecture acceptance and specification handoff: ADDED"

    Write-Host "`n=== CREATE PHASE B IMPLEMENTATION SPECIFICATION ==="

    $specDirectory = Split-Path -Parent $specPath

    if (-not (Test-Path -LiteralPath $specDirectory)) {
        New-Item `
            -ItemType Directory `
            -Path $specDirectory `
            -Force | Out-Null
    }

    $spec = @'
# v0.5 Phase B — Environment Interaction Layer specification

- **Status:** Implementation-ready specification
- **Target:** v0.5.0 Phase B, simulation-first runtime
- **Architecture authority:** [Environment Interaction Layer](../architecture/environment-interaction-layer.md)
- **Decision authority:** [ADR-006](../adr/ADR-006-environment-interaction-layer.md)
- **Governance authority:** WO-005
- **Authoritative base:** `be7502f73b51808d54728f912ead46ad0073c7b9`
- **Depends on:** implemented Phase A resource contracts
- **Runtime implementation:** not authorized by this document

## 1. Purpose

Phase B defines the provider-neutral boundary through which a resolved
operational resource may be used in a deterministic, policy-controlled,
simulation-only interaction.

The runtime specified here consumes selected Phase A `ResourceReference`
values. It does not perform resource discovery, silently repeat resource
resolution, invoke live providers, or modify external state.

The keywords **MUST**, **MUST NOT**, **SHOULD**, and **MAY** are normative.

## 2. Success boundary

The first Phase B runtime increment is complete when code can:

1. construct and serialize valid immutable interaction contracts;
2. register explicit environments and adapters in an instance-owned registry;
3. resolve one compatible environment deterministically;
4. distinguish unsupported, unavailable, incompatible, and ambiguous outcomes;
5. evaluate deterministic simulation-only policy;
6. require and validate explicit approval evidence where policy requires it;
7. invoke only a declared simulated adapter;
8. normalize bounded results and stable failures;
9. construct an immutable terminal interaction receipt;
10. preserve request, resource-resolution, workflow, execution, and interaction
    correlation;
11. prove that registration order does not alter selection;
12. prove that simulation cannot escalate to live execution;
13. prove that no filesystem, network, shell, process, database, provider SDK,
    credential, or other external I/O occurs.

Completion does not authorize integration with the current execution pipeline,
API, dashboard, benchmark suite, or any live provider.

## 3. Non-goals and exclusions

The first runtime increment MUST NOT introduce:

- live filesystem, Git, HTTP, network, shell, process, database, email,
  calendar, browser, queue, MCP, plugin, or external-agent access;
- provider SDKs, credentials, tokens, secret resolution, or secret storage;
- automatic discovery or import-time registration;
- global mutable registries;
- dynamic plugin loading;
- adaptive, learned, random, or registration-order ranking;
- background work, retries, scheduling, or long-running orchestration;
- persistent policy, approval, receipt, or idempotency storage;
- execution-pipeline, API, dashboard, or benchmark-fixture integration;
- observation generation, memory, learning, reflection, or knowledge promotion;
- catalog mutation from returned references;
- new runtime dependencies;
- real side effects.

All runtime fixtures MUST be explicitly constructed in memory.

## 4. Package boundary

A later implementation work order may authorize exactly this package:

```text
aegis_os/environment/
    __init__.py
    models.py
    errors.py
    registry.py
    resolver.py
    policy.py
    approval.py
    adapters.py
    service.py
    composition.py
```

Responsibilities:

- `models.py`: immutable contracts, enums, validation, serialization;
- `errors.py`: stable configuration and invariant exceptions;
- `registry.py`: instance-owned explicit environment/adapter registration;
- `resolver.py`: compatibility filtering and deterministic selection;
- `policy.py`: policy protocol and deterministic simulation-only evaluator;
- `approval.py`: approval protocol and deterministic in-memory evaluator;
- `adapters.py`: adapter protocol and deterministic simulated adapter;
- `service.py`: complete interaction lifecycle and receipt construction;
- `composition.py`: explicit default simulation fixture composition;
- `__init__.py`: stable public Phase B surface only.

The package MUST NOT import FastAPI, API routes, dashboard code, the legacy
orchestrator, filesystem/network/process libraries, provider packages, or
persistent storage modules.

## 5. Future implementation allowlist

A later Phase B runtime work order may modify or create only these paths:

### Runtime package

1. `aegis_os/environment/__init__.py`
2. `aegis_os/environment/models.py`
3. `aegis_os/environment/errors.py`
4. `aegis_os/environment/registry.py`
5. `aegis_os/environment/resolver.py`
6. `aegis_os/environment/policy.py`
7. `aegis_os/environment/approval.py`
8. `aegis_os/environment/adapters.py`
9. `aegis_os/environment/service.py`
10. `aegis_os/environment/composition.py`

### Focused tests

11. `tests/environment/test_models.py`
12. `tests/environment/test_registry.py`
13. `tests/environment/test_resolver.py`
14. `tests/environment/test_policy.py`
15. `tests/environment/test_approval.py`
16. `tests/environment/test_adapters.py`
17. `tests/environment/test_service.py`
18. `tests/environment/test_composition.py`

No pipeline, execution, API, dashboard, benchmark, dependency, CI, packaging,
or existing resource path is part of the first runtime allowlist.

## 6. Schema and identifier conventions

All Phase B public contracts use schema version `"1.0"`.

Identifiers MUST:

- be non-empty strings;
- contain only ASCII letters, digits, `.`, `_`, `-`, and `:`;
- be at most 128 characters;
- remain case-sensitive;
- be treated as opaque;
- be supplied by callers or deterministic injected factories;
- never be randomly generated inside registry, resolver, policy, adapter, or
  service logic.

Structured arguments, outputs, and metadata MUST be JSON-compatible, bounded,
secret-free, and recursively validated.

## 7. Exact enumerations

### 7.1 EnvironmentOperation

Stable values:

- `read`
- `list`
- `search`
- `create`
- `update`
- `delete`
- `execute`

`list` remains distinct from `search`.

### 7.2 ExecutionMode

Stable values:

- `simulation`
- `live`

The first runtime MUST reject `live` before adapter resolution or invocation.

### 7.3 SideEffectLevel

Stable values:

- `none`
- `reversible`
- `mutating`
- `destructive`
- `computational`

Operation defaults:

| Operation | Default side effect |
|---|---|
| `read` | `none` |
| `list` | `none` |
| `search` | `none` |
| `create` | `mutating` |
| `update` | `mutating` |
| `delete` | `destructive` |
| `execute` | `computational` |

A request MAY declare a stricter level but MUST NOT declare a weaker level than
the operation default.

### 7.4 EnvironmentLifecycleStatus

Stable values:

- `active`
- `unavailable`
- `disabled`

Only `active` environments are selectable.

### 7.5 EnvironmentResolutionStatus

Stable values:

- `resolved`
- `unsupported_operation`
- `no_compatible_environment`
- `ambiguous_environment`
- `unavailable_environment`
- `invalid_reference`

### 7.6 PolicyOutcome

Stable values:

- `allow`
- `deny`
- `require_approval`
- `simulation_only`
- `unsupported`

### 7.7 ApprovalState

Stable values:

- `not_required`
- `missing`
- `approved`
- `rejected`
- `expired`
- `scope_mismatch`

### 7.8 InteractionStatus

Stable terminal values:

- `success`
- `denied`
- `approval_required`
- `unsupported`
- `unavailable`
- `invalid_request`
- `timeout`
- `conflict`
- `adapter_failure`
- `partial`

Simulation is represented by `simulated: true`; it is not a status.

### 7.9 InteractionErrorCode

Stable values:

- `invalid_request`
- `unresolved_reference`
- `stale_reference`
- `incompatible_reference`
- `unsupported_operation`
- `no_compatible_environment`
- `ambiguous_environment`
- `environment_unavailable`
- `policy_denied`
- `policy_unsupported`
- `approval_required`
- `approval_rejected`
- `approval_expired`
- `approval_scope_mismatch`
- `live_mode_not_authorized`
- `missing_adapter`
- `adapter_unavailable`
- `adapter_failure`
- `malformed_adapter_result`
- `timeout`
- `conflict`
- `partial_completion`
- `simulation_mismatch`
- `duplicate_registration`
- `invalid_declaration`
- `internal_invariant_violation`

Expected domain outcomes are represented in results. Duplicate registration,
invalid declarations, and internal invariant violations raise configuration or
programming exceptions and MUST NOT masquerade as ordinary denials.

## 8. Immutable contract conventions

Public contracts SHOULD use frozen dataclasses consistent with repository
style. Collections MUST be immutable tuples or immutable mappings created from
defensive copies.

Every public contract MUST provide `to_dict()` returning JSON-compatible values
with enum values serialized as strings.

Validation MUST reject:

- blank or malformed identifiers;
- duplicate tuple members where uniqueness is required;
- mutable or non-serializable values;
- secret-like fields or forbidden keys;
- unbounded strings, arrays, mappings, outputs, or evidence;
- inconsistent operation, permission, side-effect, or execution-mode values;
- implicit live execution.

## 9. EnvironmentDefinition

Required fields:

| Field | Type | Rules |
|---|---|---|
| `environment_id` | string | stable identifier |
| `name` | string | non-blank |
| `environment_type` | string | stable provider-neutral type |
| `adapter_id` | string | registered adapter identity |
| `supported_operations` | tuple of `EnvironmentOperation` | non-empty, unique |
| `supported_resource_type_ids` | tuple of string | non-empty, unique |
| `permission_ids` | tuple of string | unique |
| `execution_modes` | tuple of `ExecutionMode` | first runtime includes only simulation |
| `maximum_side_effect` | `SideEffectLevel` | explicit |
| `trust_level` | string | stable declared value |
| `policy_profile_id` | string | stable identifier |
| `lifecycle_status` | `EnvironmentLifecycleStatus` | explicit |
| `priority` | integer | bounded, lower is preferred |
| `schema_version` | string | `"1.0"` |

Invariants:

- the environment grants no permission by declaration;
- `adapter_id` is an implementation link, not an authorization;
- `execution_modes` MUST contain `simulation` in the first runtime;
- `live` MUST NOT be present in the default composition;
- registration order has no selection meaning;
- provider credentials and clients are forbidden.

## 10. AdapterDefinition and protocol

`AdapterDefinition` fields:

- `adapter_id`;
- `name`;
- `version`;
- supported operations;
- supported resource type IDs;
- supported execution modes;
- maximum side-effect level;
- availability flag;
- schema version.

The adapter protocol exposes:

```text
definition
simulate(request, environment) -> EnvironmentResult
```

The first runtime has no live invocation method.

An adapter MUST NOT:

- reinterpret mission intent;
- resolve resources;
- select itself;
- evaluate or override policy;
- approve itself;
- broaden permissions or operation scope;
- access undeclared state;
- return provider objects, raw exceptions, or secrets;
- mutate request or environment contracts;
- produce `simulated: false`.

## 11. EnvironmentRequest

Required fields:

| Field | Type | Rules |
|---|---|---|
| `interaction_id` | string | caller supplied |
| `request_id` | string | canonical request correlation |
| `resource_resolution_id` | string | Phase A evidence link |
| `resource_references` | tuple of `ResourceReference` | non-empty |
| `operation` | `EnvironmentOperation` | explicit |
| `arguments` | bounded immutable mapping | JSON-compatible |
| `required_permission_ids` | tuple of string | unique |
| `side_effect_level` | `SideEffectLevel` | not weaker than operation |
| `execution_mode` | `ExecutionMode` | simulation only |
| `environment_id` | string/null | optional explicit constraint |
| `idempotency_key` | string/null | required for create/update/delete/execute |
| `timeout_ms` | integer/null | positive, bounded |
| `actor_id` | string | caller supplied |
| `workflow_step_id` | string/null | optional correlation |
| `execution_id` | string/null | optional correlation |
| `evidence_required` | boolean | explicit |
| `schema_version` | string | `"1.0"` |

Invariants:

- references MUST come from one successful Phase A resolution;
- resource resolution is not repeated by the service;
- raw locators, credentials, clients, policy rules, and approval decisions are
  forbidden;
- mutation and execution operations require an idempotency key;
- `execution_mode=live` is invalid for the first runtime;
- side effects are explicit and compatible;
- argument keys named `password`, `secret`, `token`, `credential`,
  `authorization`, or `api_key` are rejected case-insensitively;
- timeout is a deterministic input; the first simulated adapter does not use
  wall-clock races.

## 12. EnvironmentResolution

Required fields:

- resolution ID;
- request interaction ID;
- `EnvironmentResolutionStatus`;
- selected environment ID or null;
- selected adapter ID or null;
- ordered candidate environment IDs;
- stable reason codes;
- safe evidence;
- schema version.

Resolution is pure and side-effect free.

Candidate ordering is exactly:

1. lower declared `priority`;
2. lexicographic `environment_id`;
3. lexicographic `adapter_id`.

An explicit request environment constraint is applied before ordering.

If two distinct candidates have identical selection keys at the best rank, the
result is `ambiguous_environment`; the resolver MUST NOT choose the first.

Registration order MUST NOT affect candidates, evidence, or outcome.

## 13. Registry

`EnvironmentRegistry` is instance-owned.

It supports:

- register one environment definition and adapter instance;
- retrieve by exact ID;
- enumerate definitions in stable ID order;
- reject duplicate environment IDs;
- reject duplicate adapter IDs unless the exact same immutable object is
  intentionally supplied to the same registry operation;
- reject invalid environment-to-adapter compatibility;
- create immutable snapshots for resolution.

It MUST NOT:

- use module globals;
- scan packages;
- import plugins dynamically;
- mutate definitions after registration;
- perform availability probes with side effects;
- infer provider configuration from environment variables.

## 14. Policy boundary

The policy protocol exposes:

```text
evaluate(request, environment, resolution) -> PolicyDecision
```

`PolicyDecision` fields:

- decision ID;
- interaction ID;
- policy profile ID;
- policy version;
- `PolicyOutcome`;
- granted permission IDs;
- denied permission IDs;
- approval requirement ID or null;
- stable reason codes;
- safe evidence;
- schema version.

The default first-runtime evaluator is deterministic and simulation-only:

1. reject live mode with `deny`;
2. return `unsupported` for operation/resource incompatibility;
3. deny any required permission not declared by the environment fixture;
4. deny side effects above the environment maximum;
5. return `require_approval` for configured mutating, destructive, or
   computational fixtures;
6. otherwise return `simulation_only`.

`simulation_only` permits only a simulated adapter invocation and MUST produce
`simulated: true`.

Policy evaluation occurs after environment resolution and before approval or
adapter invocation.

## 15. Approval boundary

`ApprovalRequirement` fields:

- requirement ID;
- exact interaction ID;
- actor ID;
- operation;
- resource reference IDs;
- environment ID;
- required permission IDs;
- maximum side-effect level;
- policy profile/version;
- issue and expiry values supplied as deterministic inputs;
- one-time boolean;
- schema version.

`ApprovalEvidence` fields:

- approval ID;
- requirement ID;
- approver ID;
- `ApprovalState`;
- exact bound scope;
- policy version;
- issued/expiry inputs;
- schema version.

The approval evaluator:

- returns `not_required` when policy does not require approval;
- returns `missing` when no evidence is supplied;
- validates exact requirement, request, resource, environment, permission,
  operation, side-effect, and policy-version scope;
- returns `expired` using an injected deterministic current-time value;
- cannot override `deny`, `unsupported`, or scope mismatch;
- performs no persistence.

## 16. EnvironmentResult

Required fields:

| Field | Type | Rules |
|---|---|---|
| `result_id` | string | caller/factory supplied |
| `interaction_id` | string | exact request link |
| `status` | `InteractionStatus` | terminal |
| `simulated` | boolean | always true in first runtime |
| `output` | bounded immutable mapping/null | normalized |
| `returned_references` | tuple of `ResourceReference` | no catalog mutation |
| `error_code` | `InteractionErrorCode`/null | required on failure |
| `reason_codes` | tuple of string | stable order |
| `safe_metadata` | bounded immutable mapping | secret-free |
| `adapter_id` | string/null | attribution |
| `environment_id` | string/null | attribution |
| `duration_ms` | integer/null | supplied deterministic fixture or null |
| `schema_version` | string | `"1.0"` |

`success` and `partial` MAY contain output. Failure statuses MUST NOT expose raw
exceptions or unbounded provider payloads.

The service MUST reject an adapter result when:

- interaction, adapter, or environment identity does not match;
- `simulated` is false;
- status or error fields are inconsistent;
- output or metadata exceeds bounds;
- forbidden keys or values are present;
- returned references are malformed;
- schema version is unsupported.

Malformed results become a normalized `adapter_failure` result with
`malformed_adapter_result`.

## 17. InteractionReceipt

The terminal immutable receipt contains:

- receipt ID;
- interaction and request IDs;
- resource-resolution ID;
- workflow-step and execution IDs where supplied;
- request summary;
- target reference summaries;
- environment-resolution summary;
- selected environment and adapter attribution;
- policy decision;
- approval requirement and approval state;
- normalized result summary;
- `simulated`;
- ordered safe evidence events;
- terminal status and error code;
- supplied timestamp values or null;
- schema version.

Evidence events have:

- sequence integer;
- stable event type;
- source component;
- reason code;
- safe bounded detail mapping.

Evidence ordering follows lifecycle order, never dictionary or registration
order.

Receipts exclude:

- credentials, tokens, secrets;
- raw arguments marked sensitive;
- raw exceptions and tracebacks;
- provider objects;
- unbounded outputs;
- mutable references;
- hidden policy or approval state.

A receipt is constructed once after a terminal outcome and cannot be modified
by adapters or later cognition.

## 18. Lifecycle service

`EnvironmentInteractionService.interact()` performs exactly:

1. validate `EnvironmentRequest`;
2. reject live execution;
3. validate supplied resolved references without re-resolving;
4. validate operation/resource compatibility;
5. resolve environment and adapter deterministically;
6. normalize resolution failure when terminal;
7. evaluate policy;
8. normalize policy denial or unsupported outcome when terminal;
9. evaluate approval requirement/evidence;
10. normalize approval failure when terminal;
11. invoke the selected simulated adapter;
12. validate and normalize adapter result;
13. construct immutable ordered evidence;
14. construct immutable terminal receipt;
15. return one aggregate interaction response containing result and receipt.

No lifecycle stage may be skipped by an adapter.

The service does not retry. Retryability may be recorded as safe metadata, but
a later work order must define retry orchestration.

## 19. Aggregate response

The service returns an immutable `InteractionResponse` containing:

- request;
- environment resolution;
- policy decision or null;
- approval state;
- normalized result;
- terminal receipt;
- schema version.

The aggregate exists for caller convenience. Result and receipt remain
separate contracts with separate semantics.

## 20. Determinism

For fixed:

- registry snapshot;
- request;
- resolved references;
- policy fixture;
- approval evidence;
- simulated adapter fixture;
- injected IDs and timestamps;

the system MUST produce equal:

- candidate ordering;
- selected environment and adapter;
- resolution status and reasons;
- policy outcome and evidence;
- approval state;
- result status, output, and reasons;
- receipt structure and evidence ordering;
- serialized dictionaries.

Tests MUST repeat equivalent inputs under reversed registration order.

No random UUID, implicit clock, hash-order dependency, global registry, network
state, or provider state may influence deterministic outputs.

## 21. Bounds and security

Initial normative bounds:

- identifier: 128 characters;
- display name: 256 characters;
- description/reason text: 2,000 characters;
- argument/output/metadata mapping depth: 8;
- mapping entries per level: 100;
- collection members: 100;
- string value: 20,000 characters;
- resource references per request: 20;
- reason codes per contract: 50;
- evidence events per receipt: 100;
- serialized result or receipt: 1 MiB.

Oversized input is `invalid_request`. Oversized or malformed adapter output is
`malformed_adapter_result`.

Provider or resource output is untrusted data. It MUST NOT be treated as
instruction, configuration, policy, approval, or executable content.

## 22. Idempotency and replay

`create`, `update`, `delete`, and `execute` require an idempotency key even in
simulation.

The first runtime validates and records the key but does not persist replay
state. Therefore:

- the service MUST NOT claim cross-process replay prevention;
- repeated identical simulation inputs remain deterministic;
- conflicting reuse detection is limited to an optional explicit in-memory
  fixture supplied to one service instance;
- durable replay protection is deferred to a later persistence work order.

## 23. Timeout and cancellation

`timeout_ms` is a validated request constraint.

The first simulated adapter MAY use deterministic fixtures to return `timeout`.
It MUST NOT depend on real sleep, thread races, background tasks, or elapsed
wall-clock behavior.

Cancellation is represented only as a future protocol extension. No
cancellation state or background execution is implemented in the first
runtime.

## 24. Partial results

`partial` is valid only when:

- the operation semantically permits multiple bounded items;
- at least one normalized item succeeded;
- at least one item failed or was omitted;
- output identifies successful items without leaking raw errors;
- error code is `partial_completion`;
- receipt evidence contains stable per-item summaries.

Single-target mutation operations MUST NOT return `partial` in the first
runtime.

## 25. Resource subsystem handoff

The runtime consumes `ResourceReference` values and the successful
`resource_resolution_id`.

It MAY validate:

- reference schema;
- resource type compatibility;
- expected version selector;
- declared lifecycle/freshness information supplied by the caller.

It MUST NOT:

- query or mutate `ResourceCatalog`;
- perform requirement matching;
- silently choose a different resource;
- treat resource permissions as authorization;
- persist returned references.

Returned references are evidence only until a later explicit catalog-update
boundary is authorized.

## 26. Current execution boundary

The first runtime is not called by:

- `CognitiveRuntime`;
- the canonical pipeline;
- `Kernel`;
- `ExecutionEngine`;
- FastAPI routes;
- dashboard JavaScript;
- benchmark CLI.

Execution integration requires a later specification amendment and work order.
That later work must define step-to-interaction mapping, aggregate failure
semantics, receipt embedding/reference limits, and cancellation/budget policy.

## 27. Error handling

Expected domain failures return normalized results and receipts.

Configuration/programming failures raise typed exceptions:

- `DuplicateRegistrationError`;
- `InvalidDeclarationError`;
- `InternalInvariantError`.

Adapter exceptions are caught at the service boundary and normalized to
`adapter_failure`; raw exception messages are not serialized.

The service MUST still construct a terminal receipt for every validated request
that reaches lifecycle processing, including resolution, policy, approval, and
adapter failures.

## 28. Public exports

`aegis_os.environment` exports only:

- stable enums;
- immutable public contracts;
- registry;
- resolver;
- policy and approval protocols;
- simulated adapter protocol/fixture;
- lifecycle service;
- explicit simulation composition factory.

Internal validators, mutable builders, fixtures, and helper exceptions are not
part of the stable public surface unless explicitly listed by the later
implementation work order.

## 29. Test obligations

### Models

Tests cover:

- valid construction and serialization;
- every enum value;
- identifier and bounds validation;
- immutable/default-factory safety;
- operation/side-effect compatibility;
- idempotency requirements;
- secret-key rejection;
- live-mode rejection;
- result/error consistency;
- receipt immutability and evidence ordering.

### Registry

Tests cover:

- explicit registration;
- duplicate environment and adapter rejection;
- instance isolation;
- stable enumeration;
- invalid environment/adapter declarations;
- no import-time or global behavior.

### Resolver

Tests cover:

- deterministic selection;
- explicit environment constraint;
- operation/resource/mode/side-effect filtering;
- unavailable and disabled environments;
- unsupported operation;
- no compatible environment;
- ambiguity;
- reversed registration-order equivalence.

### Policy

Tests cover:

- default simulation-only outcome;
- missing permission denial;
- side-effect denial;
- live-mode denial;
- unsupported outcome;
- approval requirement;
- adapter cannot bypass policy.

### Approval

Tests cover:

- not required;
- missing;
- approved;
- rejected;
- expired;
- scope mismatch;
- policy version mismatch;
- denial cannot be overridden.

### Adapters

Tests cover:

- deterministic outputs;
- every supported operation fixture;
- declared-support enforcement;
- unavailable fixture;
- timeout fixture;
- conflict fixture;
- partial fixture;
- malformed result;
- raw exception normalization;
- simulation flag enforcement;
- no external I/O.

### Service

Tests cover every lifecycle terminal:

- invalid request;
- invalid/stale/incompatible reference;
- unsupported operation;
- no environment;
- ambiguity;
- policy denial;
- approval required/rejected/expired;
- missing adapter;
- unavailable adapter;
- timeout;
- conflict;
- partial completion;
- adapter failure;
- malformed adapter result;
- successful simulation;
- complete correlation;
- immutable receipt;
- deterministic repeated equality;
- registration-order independence;
- policy/approval bypass prevention;
- simulation-to-live escalation prevention.

### Composition

Tests prove:

- explicit fixture construction;
- isolated registries per factory call;
- simulation-only adapters;
- no credentials or provider clients;
- no network/filesystem/process/database imports or actions.

The complete repository suite, Ruff lint, Ruff format, dependency integrity,
and `git diff --check` remain mandatory.

## 30. Benchmark obligations

The first runtime work order does not modify benchmark paths.

A later benchmark work order SHOULD add deterministic optional criteria for:

- environment selection;
- operation compatibility;
- policy outcome;
- approval requirement;
- adapter resolution;
- failure taxonomy;
- receipt completeness;
- correlation;
- simulation enforcement.

Benchmark scoring MUST NOT grade live content quality, provider availability, or
subjective adapter output.

## 31. Acceptance criteria for the future runtime

A future implementation candidate is eligible for review only when:

1. it descends from the exact separately authorized base;
2. only the 18 future implementation allowlist paths differ;
3. all contracts use schema version `1.0`;
4. all public contracts are immutable and serializable;
5. registry state is instance-owned and explicit;
6. selection is independent of registration order;
7. policy precedes approval and invocation;
8. adapters cannot authorize or approve themselves;
9. live mode is rejected structurally;
10. every terminal path has normalized result and immutable receipt;
11. evidence is ordered, bounded, and secret-free;
12. no external I/O or provider dependency exists;
13. no current pipeline, execution, API, dashboard, benchmark, or resource
    behavior changes;
14. focused tests and the complete repository suite pass;
15. Ruff, dependency, and whitespace checks pass;
16. the candidate worktree is clean;
17. no main, remote, tag, release, ruleset, or unrelated worktree changes.

## 32. Deferred decisions

These decisions are intentionally deferred and are not required for the first
simulation-only runtime:

- live adapter invocation protocol;
- credential and secret retrieval;
- persistent approvals;
- durable idempotency/replay storage;
- persistent receipts;
- execution-step integration;
- cancellation and background orchestration;
- retry and budget policy;
- observation generation;
- catalog updates from returned references;
- provider-specific environment types;
- API/dashboard surfaces;
- benchmark fixture implementation;
- memory, learning, and reflection integration.

Each requires separate architecture, threat model, implementation boundary, and
governance authority.

## 33. Governance boundary

This specification is a design artifact. It grants no authority to:

- modify Python or tests;
- create runtime modules;
- integrate a deliverable into `main`;
- push or publish a deliverable;
- invoke providers;
- create tags or releases;
- modify rulesets;
- clean up branches or worktrees.

Runtime implementation begins only after separate explicit activation of an
implementation work order using the exact accepted allowlist.
'@

    [System.IO.File]::WriteAllText(
        $specPath,
        $spec.TrimEnd() + "`n",
        $utf8NoBom
    )

    Write-Host "Phase B implementation-ready specification: CREATED"

    Write-Host "`n=== UPDATE ROADMAP ==="

    $roadmap = [System.IO.File]::ReadAllText($roadmapPath)
    $roadmap = $roadmap -replace "`r`n", "`n"

    $oldRoadmapState = @'
Phase A is implemented. Phase B architecture is proposed; its runtime is not
implemented. See the current
[Environment Interaction Layer architecture](../architecture/environment-interaction-layer.md).
'@

    $newRoadmapState = @'
Phase A is implemented. Phase B architecture is accepted and its
implementation specification is defined; its runtime is not implemented. See
the accepted
[Environment Interaction Layer architecture](../architecture/environment-interaction-layer.md)
and the
[Phase B implementation specification](../specifications/v0.5-phase-b-environment-interaction-layer.md).
'@

    $roadmap = Replace-ExactlyOnce `
        -Text $roadmap `
        -OldValue $oldRoadmapState `
        -NewValue $newRoadmapState `
        -Label "roadmap Phase B state"

    [System.IO.File]::WriteAllText(
        $roadmapPath,
        $roadmap,
        $utf8NoBom
    )

    Write-Host "Roadmap Phase B status: UPDATED"

    Write-Host "`n=== VALIDATE FOUR-PATH DELIVERABLE ==="

    $changedPaths = @(
        git -C $worktree status --short |
            ForEach-Object { $_.Substring(3) }
    )

    Assert-ExactPathSet `
        -Actual $changedPaths `
        -Expected $expectedPaths `
        -Label "WO-005 deliverable"

    Invoke-Native {
        git -C $worktree diff --check
    } "WO-005 whitespace validation"

    foreach ($path in $expectedPaths) {
        if (-not (Test-Path -LiteralPath (Join-Path $worktree $path))) {
            throw "Expected deliverable path is missing: $path"
        }
    }

    $adrFinal = [System.IO.File]::ReadAllText($adrPath)
    $architectureFinal = [System.IO.File]::ReadAllText($architecturePath)
    $specFinal = [System.IO.File]::ReadAllText($specPath)
    $roadmapFinal = [System.IO.File]::ReadAllText($roadmapPath)

    if (-not $adrFinal.Contains("- **Status:** Accepted")) {
        throw "ADR-006 is not accepted in the deliverable."
    }

    if (-not $architectureFinal.Contains(
        "> **Status: Accepted architecture; runtime not implemented.**"
    )) {
        throw "The architecture status was not reconciled."
    }

    foreach ($requiredText in @(
        "## 5. Future implementation allowlist",
        "aegis_os/environment/service.py",
        "tests/environment/test_service.py",
        "PolicyOutcome",
        "InteractionErrorCode",
        "simulated: true",
        "Runtime implementation begins only after separate explicit activation"
    )) {
        if (-not $specFinal.Contains($requiredText)) {
            throw "Required specification content is missing: $requiredText"
        }
    }

    if (-not $roadmapFinal.Contains(
        "Phase B architecture is accepted"
    )) {
        throw "The roadmap does not record the accepted architecture."
    }

    $sourceCodeChanges = @(
        git -C $worktree diff --name-only $base -- `
            aegis_os `
            tests `
            pyproject.toml `
            .github
    )

    if ($sourceCodeChanges.Count -ne 0) {
        throw "The deliverable changed executable, test, dependency, or CI paths."
    }

    Write-Host "Exact four-path boundary, content, links, and zero-code delta: PASS"

    Write-Host "`n=== COMMIT WO-005 DELIVERABLE ==="

    Invoke-Native {
        git -C $worktree add -- $expectedPaths
    } "WO-005 deliverable staging"

    $stagedPaths = @(
        git -C $worktree diff --cached --name-only
    )

    Assert-ExactPathSet `
        -Actual $stagedPaths `
        -Expected $expectedPaths `
        -Label "Staged WO-005 deliverable"

    Invoke-Native {
        git -C $worktree diff --cached --check
    } "Staged WO-005 whitespace validation"

    Invoke-Native {
        git -C $worktree commit -m $commitSubject
    } "WO-005 deliverable commit creation"

    $deliverableCommit = (
        git -C $worktree rev-parse HEAD
    ).Trim()

    $deliverableParent = (
        git -C $worktree rev-parse HEAD^
    ).Trim()

    $deliverableTree = (
        git -C $worktree rev-parse HEAD^{tree}
    ).Trim()

    $deliverableSubject = (
        git -C $worktree log -1 --format=%s
    ).Trim()

    $committedPaths = @(
        git -C $worktree diff-tree `
            --no-commit-id `
            --name-only `
            -r `
            HEAD
    )

    if ($deliverableParent -ne $base) {
        throw "WO-005 deliverable parent mismatch."
    }

    if ($deliverableSubject -ne $commitSubject) {
        throw "WO-005 deliverable subject mismatch."
    }

    Assert-ExactPathSet `
        -Actual $committedPaths `
        -Expected $expectedPaths `
        -Label "Committed WO-005 deliverable"

    if (@(git -C $worktree status --short).Count -ne 0) {
        throw "WO-005 deliverable worktree is not clean after commit."
    }

    Write-Host "Bounded documentation deliverable commit: CREATED"

    Write-Host "`n=== DESIGNATE CANONICAL CANDIDATE FOR REVIEW ==="

    if (Test-Path -LiteralPath $reviewWorktree) {
        throw "WO-005 review worktree already exists: $reviewWorktree"
    }

    if (@(git -C $repo branch --list $reviewBranch).Count -ne 0) {
        throw "WO-005 review branch already exists: $reviewBranch"
    }

    Invoke-Native {
        git -C $repo worktree add `
            -b $reviewBranch `
            $reviewWorktree `
            $authorizationMain
    } "WO-005 review worktree creation"

    $workOrderPath = Join-Path $reviewWorktree $workOrderRelative
    $traceabilityPath = Join-Path $reviewWorktree $traceabilityRelative

    $workOrder = [System.IO.File]::ReadAllText($workOrderPath)
    $workOrder = $workOrder -replace "`r`n", "`n"

    if ($workOrder.Contains("## Candidate designation")) {
        throw "WO-005 already contains a candidate designation."
    }

    $workOrder = Replace-ExactlyOnce `
        -Text $workOrder `
        -OldValue "**Status:** ACTIVE - ARCHITECTURE AND SPECIFICATION WORK AUTHORIZED" `
        -NewValue "**Status:** ACTIVE - CANDIDATE DESIGNATED FOR REVIEW" `
        -Label "WO-005 designation status"

    $oldDisposition = @'
WO-005: ACTIVE - ARCHITECTURE AND SPECIFICATION WORK AUTHORIZED
Authoritative base: be7502f73b51808d54728f912ead46ad0073c7b9
Deliverable scope: FOUR DOCUMENTATION PATHS
Deliverable candidate designated: NO
Architecture review: NOT STARTED
QA review: NOT STARTED
Deliverable integration authority: NOT GRANTED
Deliverable publication authority: NOT GRANTED
Runtime implementation authority: NOT GRANTED
'@

    $newDisposition = @"
WO-005: ACTIVE - CANDIDATE DESIGNATED FOR REVIEW
Authoritative base: $base
Authorization main: $authorizationMain
Deliverable scope: FOUR DOCUMENTATION PATHS
Deliverable candidate designated: $deliverableCommit
Candidate tree: $deliverableTree
Architecture review: PENDING
QA review: PENDING
Deliverable integration authority: NOT GRANTED
Deliverable publication authority: NOT GRANTED
Runtime implementation authority: NOT GRANTED
"@

    $workOrder = Replace-ExactlyOnce `
        -Text $workOrder `
        -OldValue $oldDisposition `
        -NewValue $newDisposition.TrimEnd() `
        -Label "WO-005 current disposition"

    $candidateSection = @"

## Candidate designation

- Designation date: 2026-07-31
- Authoritative base: ``$base``
- Published authorization main: ``$authorizationMain``
- Canonical reviewed candidate: ``$deliverableCommit``
- Canonical candidate parent: ``$deliverableParent``
- Canonical candidate tree: ``$deliverableTree``
- Candidate subject: ``$deliverableSubject``
- Changed-path count: 4
- Executable-code changes: 0
- Test changes: 0
- Dependency changes: 0
- CI changes: 0
- Candidate worktree clean: yes
- Architecture review: pending
- QA review: pending
- Integration authority: not granted
- Publication authority: not granted
- Runtime implementation authority: not granted

### Canonical changed paths

1. ``docs/adr/ADR-006-environment-interaction-layer.md``
2. ``docs/architecture/environment-interaction-layer.md``
3. ``docs/specifications/v0.5-phase-b-environment-interaction-layer.md``
4. ``docs/roadmap/ROADMAP.md``

This designation authorizes review of the immutable canonical candidate only.
It does not authorize correction, integration, publication, runtime
implementation, push, main modification, tag, release, ruleset change, or
cleanup.
"@

    $workOrder = $workOrder.TrimEnd() + $candidateSection + "`n"

    $traceability = [System.IO.File]::ReadAllText($traceabilityPath)
    $traceability = $traceability -replace "`r`n", "`n"

    if ($traceability.Contains("## TR-008 WO-005 Candidate Designation")) {
        throw "TR-008 candidate designation already exists."
    }

    $traceabilitySection = @"

## TR-008 WO-005 Candidate Designation

- Work order: WO-005 - Environment Interaction Layer Architecture Acceptance and Implementation Specification
- Designation date: 2026-07-31
- Authoritative base: ``$base``
- Published authorization main: ``$authorizationMain``
- Canonical reviewed candidate: ``$deliverableCommit``
- Canonical parent: ``$deliverableParent``
- Canonical tree: ``$deliverableTree``
- Candidate changed paths: exactly four authorized documentation paths
- Executable, test, dependency, and CI changes: none
- Candidate state: **DESIGNATED FOR REVIEW**
- Architecture review: pending
- QA review: pending
- Integration authority: not granted
- Publication authority: not granted
- Runtime implementation authority: not granted

Review must evaluate this immutable SHA and tree. Any content correction creates
a new candidate and requires redesignation.
"@

    $traceability = $traceability.TrimEnd() + $traceabilitySection + "`n"

    [System.IO.File]::WriteAllText(
        $workOrderPath,
        $workOrder,
        $utf8NoBom
    )

    [System.IO.File]::WriteAllText(
        $traceabilityPath,
        $traceability,
        $utf8NoBom
    )

    $reviewChangedPaths = @(
        git -C $reviewWorktree status --short |
            ForEach-Object { $_.Substring(3) }
    )

    Assert-ExactPathSet `
        -Actual $reviewChangedPaths `
        -Expected $governancePaths `
        -Label "WO-005 candidate designation governance"

    Invoke-Native {
        git -C $reviewWorktree diff --check
    } "WO-005 designation whitespace validation"

    Invoke-Native {
        git -C $reviewWorktree add -- $governancePaths
    } "WO-005 designation staging"

    $stagedGovernancePaths = @(
        git -C $reviewWorktree diff --cached --name-only
    )

    Assert-ExactPathSet `
        -Actual $stagedGovernancePaths `
        -Expected $governancePaths `
        -Label "Staged WO-005 candidate designation"

    Invoke-Native {
        git -C $reviewWorktree diff --cached --check
    } "Staged WO-005 designation validation"

    Invoke-Native {
        git -C $reviewWorktree commit -m $designationSubject
    } "WO-005 candidate designation commit creation"

    $designationCommit = (
        git -C $reviewWorktree rev-parse HEAD
    ).Trim()

    $designationParent = (
        git -C $reviewWorktree rev-parse HEAD^
    ).Trim()

    $designationTree = (
        git -C $reviewWorktree rev-parse "HEAD^{tree}"
    ).Trim()

    if ($designationParent -ne $authorizationMain) {
        throw "WO-005 designation commit parent mismatch."
    }

    if (@(git -C $reviewWorktree status --short).Count -ne 0) {
        throw "WO-005 review worktree is not clean after designation commit."
    }

    Write-Host "Canonical candidate and governance designation: CREATED"

    Write-Host "`n=== FINAL PRESERVATION AND MANIFEST ==="

    Invoke-Native {
        git -C $repo fetch origin `
            "+refs/heads/main:refs/remotes/origin/main"
    } "Final remote refresh"

    $finalRemote = Get-LiveRemoteMain $repo
    $finalTracking = (
        git -C $repo rev-parse refs/remotes/origin/main
    ).Trim()

    $finalLocalMain = (
        git -C $repo rev-parse refs/heads/main
    ).Trim()

    foreach ($identity in @(
        $finalRemote,
        $finalTracking,
        $finalLocalMain
    )) {
        if ($identity -ne $authorizationMain) {
            throw "Main or remote changed during WO-005 candidate creation."
        }
    }

    Assert-AllWorktreesClean $repo

    New-Item `
        -ItemType Directory `
        -Path $logDirectory `
        -Force | Out-Null

    $manifest = @"
AEGIS WO-005 Candidate Designation
==================================

Date: 2026-07-31
Authoritative architectural base: $base
Published WO-005 authorization main: $authorizationMain

Canonical candidate:
Commit: $deliverableCommit
Parent: $deliverableParent
Tree: $deliverableTree
Subject: $deliverableSubject
Branch: $branch
Worktree: $worktree

Governance designation:
Commit: $designationCommit
Parent: $designationParent
Tree: $designationTree
Subject: $designationSubject
Branch: $reviewBranch
Worktree: $reviewWorktree

Validation:
- Exact four-document candidate boundary: PASS
- Exact two-file governance designation boundary: PASS
- Executable code changes: 0
- Test changes: 0
- Dependency changes: 0
- CI changes: 0
- Whitespace validation: PASS
- Worktrees clean: PASS
- Local main unchanged: PASS
- origin/main unchanged: PASS
- Live remote main unchanged: PASS
- Push performed: NO
- Integration authorized: NO
- Publication authorized: NO
- Runtime implementation authorized: NO
"@

    [System.IO.File]::WriteAllText(
        $manifestPath,
        $manifest,
        $utf8NoBom
    )

    Write-Host "`n=== WO-005 CANDIDATE DESIGNATION RESULT ==="

    [pscustomobject]@{
        AuthoritativeBase = $base
        AuthorizationMain = $authorizationMain
        CanonicalCandidate = $deliverableCommit
        CanonicalCandidateParent = $deliverableParent
        CanonicalCandidateTree = $deliverableTree
        CanonicalCandidateSubject = $deliverableSubject
        CanonicalPathCount = $committedPaths.Count
        ADR006Status = "ACCEPTED IN CANDIDATE"
        ArchitectureStatus = "ACCEPTED IN CANDIDATE"
        SpecificationStatus = "IMPLEMENTATION-READY"
        FutureRuntimePathCount = 18
        ExecutableCodeChanges = 0
        TestChanges = 0
        DependencyChanges = 0
        CIChanges = 0
        DesignationCommit = $designationCommit
        DesignationParent = $designationParent
        DesignationTree = $designationTree
        GovernancePathCount = $stagedGovernancePaths.Count
        LocalMain = $finalLocalMain
        OriginMain = $finalTracking
        LiveRemoteMain = $finalRemote
        RemoteMutation = "NONE"
        WorktreesClean = $true
        Manifest = $manifestPath
        ArchitectureReview = "PENDING"
        QAReview = "PENDING"
        IntegrationAuthorized = $false
        PublicationAuthorized = $false
        RuntimeImplementationAuthorized = $false
        FinalStatus = "WO-005 CANDIDATE DESIGNATED FOR REVIEW"
    } | Format-List

    Write-Host "Canonical deliverable paths:"
    $committedPaths | ForEach-Object { Write-Host " - $_" }

    Write-Host "`nWO-005 CANDIDATE DESIGNATION: COMPLETE"
    Write-Host "The canonical four-document candidate is created and designated for review."
    Write-Host "No push, main update, integration, runtime implementation, tag, release, ruleset change, or cleanup was performed."

}
catch {
    if (Test-Path -LiteralPath $worktree) {
        Write-Host "`nWO-005 deliverable worktree preserved for diagnosis:"
        git -C $worktree status --short
    }

    throw
}
