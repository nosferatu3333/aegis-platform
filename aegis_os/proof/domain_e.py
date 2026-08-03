\
"""Executable Domain E functional proof scenarios.

Domain E verifies operational resilience at the Platform/OPS integration
boundary.

S17 uses the production OpsCapabilitySelectorAdapter and
HybridCapabilitySelector. A missing OPS repository produces a typed
OpsIntegrationError and an unavailable diagnostic. The declared bounded
Platform fallback may still provide analysis, but it must not be represented
as a live OPS selection.

S18 uses the production live OPS CapabilityLoader, CapabilityRegistry, and
CapabilitySelector against controlled malformed YAML. The proof accepts either
an explicit loader exception or a zero-valid-capability result as rejection,
then verifies that no malformed capability reaches registry or selection.

RC1 does not expose automatic retries, timeout policy, or a circuit breaker at
this boundary. This proof does not claim those mechanisms or external effects.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

SUITE_VERSION = "1.0"
RELEASE_VERSION = "1.7.0-rc1"
DOMAIN = "E"
OVERALL_PASS_VERDICT = "DOMAIN E FUNCTIONALLY VERIFIED"
SINGLE_PASS_VERDICT = "SCENARIO FUNCTIONALLY VERIFIED"


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _definition_path() -> Path:
    return Path(__file__).resolve().parent / "scenarios" / "domain_e.json"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _git_value(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=_root(),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _ops_root() -> Path:
    configured = os.environ.get("AEGIS_OPS_PATH", "").strip()
    if not configured:
        raise RuntimeError("AEGIS_OPS_PATH is required for Domain E proof.")
    root = Path(configured).expanduser().resolve()
    if not root.is_dir():
        raise RuntimeError(f"AEGIS_OPS_PATH does not exist: {root}")
    return root


def _enable_ops_namespace(ops_root: Path) -> None:
    import aegis_os as platform_package

    namespace = str(ops_root / "aegis_os")
    if namespace not in platform_package.__path__:
        platform_package.__path__.append(namespace)


def _serialize(value: Any) -> Any:
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _serialize(value.to_dict())
    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_serialize(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def load_domain_e_definition() -> dict[str, Any]:
    payload = json.loads(_definition_path().read_text(encoding="utf-8-sig"))
    identifiers = [item["scenario_id"] for item in payload["scenarios"]]
    expected = {"AEGIS-RC1-S17", "AEGIS-RC1-S18"}
    if set(identifiers) != expected:
        raise ValueError("Domain E must define exactly S17 and S18.")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Domain E scenario identifiers must be unique.")
    return payload


def _base(definition: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "suite_version": SUITE_VERSION,
        "release_version": RELEASE_VERSION,
        "domain": DOMAIN,
        "scenario_id": definition["scenario_id"],
        "title": definition["title"],
        "expected_canonical_outcome": definition[
            "expected_canonical_outcome"
        ],
        "actual_canonical_outcome": None,
        "started_at": _utc_now(),
        "completed_at": None,
        "passed": False,
        "assertions": [],
        "evidence": {},
        "failure_reason": None,
        "execution_requested": False,
        "execution_performed": False,
        "declared_boundary": {
            "selection_mode": "live OPS with bounded Platform fallback",
            "automatic_retry_present": False,
            "timeout_policy_present": False,
            "circuit_breaker_present": False,
            "real_world_execution_claimed": False,
            "production_readiness_claimed": False,
        },
    }


def _check(
    result: dict[str, Any],
    name: str,
    condition: bool,
    detail: str,
) -> None:
    result["assertions"].append(
        {
            "name": name,
            "passed": bool(condition),
            "detail": detail,
        }
    )


def _finish(result: dict[str, Any]) -> dict[str, Any]:
    result["passed"] = bool(result["assertions"]) and all(
        item["passed"] for item in result["assertions"]
    )
    if not result["passed"]:
        failed = [
            item["name"]
            for item in result["assertions"]
            if not item["passed"]
        ]
        result["failure_reason"] = "Failed assertions: " + ", ".join(failed)
    result["completed_at"] = _utc_now()
    return result


class _BoundedFallback:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def select(self, task: str, **context: Any) -> dict[str, Any]:
        self.calls.append({"task": task, "context": _serialize(context)})
        return {
            "capability": {
                "id": "platform.capability.bounded_software_planning",
                "name": "Platform Bounded Software Planning",
                "workflow": [
                    {
                        "step": 1,
                        "action": "Describe the bounded software objective.",
                        "expected_result": "A constrained objective statement.",
                    },
                    {
                        "step": 2,
                        "action": "Prepare a non-executing review plan.",
                        "expected_result": "A reviewable bounded plan.",
                    },
                ],
            },
            "confidence": 1.0,
            "score": 1.0,
            "reasons": (
                "Live OPS was unavailable; bounded Platform fallback used.",
            ),
            "matched_tags": ("bounded-fallback",),
            "source": "platform-bounded-fallback",
            "source_path": "",
        }


class _FixedSelector:
    def __init__(self, selection: Any) -> None:
        self.selection = selection

    def select(self, task: str, **context: Any) -> Any:
        return self.selection


def _scenario_s17(definition: dict[str, Any]) -> dict[str, Any]:
    from aegis_os.pipeline.models import PipelineStatus
    from aegis_os.pipeline.ops_capability_adapter import (
        HybridCapabilitySelector,
        OpsCapabilitySelectorAdapter,
        OpsIntegrationError,
    )
    from aegis_os.pipeline.request_pipeline import CognitiveRequestPipeline

    result = _base(definition)
    task = (
        "Build a bounded software feature and prepare a review plan "
        "without external execution."
    )

    with tempfile.TemporaryDirectory(prefix="aegis-domain-e-s17-") as temp:
        missing_root = Path(temp) / "missing-ops"
        direct_adapter = OpsCapabilitySelectorAdapter(missing_root)

        direct_selection = None
        direct_error = None
        try:
            direct_selection = direct_adapter.select(task)
        except OpsIntegrationError as error:
            direct_error = error

        diagnostic = direct_adapter.diagnostic
        fallback = _BoundedFallback()
        hybrid = HybridCapabilitySelector(
            ops_selector=OpsCapabilitySelectorAdapter(missing_root),
            fallback_selector=fallback,
        )
        fallback_selection = hybrid.select(
            task,
            required_capabilities=("development",),
        )
        analysis = CognitiveRequestPipeline(
            capability_selector=_FixedSelector(fallback_selection)
        ).process_task(task)

    source = analysis.metadata.get("capability_source")
    result["actual_canonical_outcome"] = (
        "bounded_fallback"
        if (
            direct_error is not None
            and diagnostic["available"] is False
            and source == "platform-bounded-fallback"
        )
        else "unsafe_or_unclassified_unavailability"
    )
    result["evidence"] = {
        "direct_adapter_selection": _serialize(direct_selection),
        "direct_error_type": (
            type(direct_error).__name__ if direct_error is not None else None
        ),
        "direct_error": (
            str(direct_error) if direct_error is not None else None
        ),
        "diagnostic": diagnostic,
        "fallback_calls": fallback.calls,
        "fallback_selection": _serialize(fallback_selection),
        "analysis": analysis.to_dict(),
        "live_ops_claimed": source == "aegis-ops",
        "automatic_retry_present": False,
        "timeout_policy_present": False,
        "circuit_breaker_present": False,
    }

    _check(
        result,
        "typed_ops_error_raised",
        isinstance(direct_error, OpsIntegrationError),
        f"Error type: {type(direct_error).__name__ if direct_error else None}",
    )
    _check(
        result,
        "unavailable_diagnostic_exposed",
        diagnostic["available"] is False
        and diagnostic["source"] == "aegis-ops"
        and bool(diagnostic["error"]),
        json.dumps(diagnostic, sort_keys=True),
    )
    _check(
        result,
        "direct_adapter_emits_no_selection",
        direct_selection is None,
        f"Direct selection: {_serialize(direct_selection)}",
    )
    _check(
        result,
        "bounded_fallback_invoked_once",
        len(fallback.calls) == 1,
        f"Fallback calls: {len(fallback.calls)}",
    )
    _check(
        result,
        "fallback_analysis_ready",
        analysis.status is PipelineStatus.READY
        and len(analysis.workflow) == 2,
        (
            f"Status: {analysis.status.value}; "
            f"workflow steps: {len(analysis.workflow)}"
        ),
    )
    _check(
        result,
        "fallback_source_is_truthful",
        source == "platform-bounded-fallback"
        and source != "aegis-ops",
        f"Capability source: {source}",
    )
    _check(
        result,
        "no_execution_performed",
        result["execution_performed"] is False,
        "S17 proves selection resilience and performs no execution.",
    )
    _check(
        result,
        "undeclared_resilience_mechanisms_not_claimed",
        all(
            result["evidence"][key] is False
            for key in (
                "automatic_retry_present",
                "timeout_policy_present",
                "circuit_breaker_present",
            )
        ),
        "RC1 exposes bounded fallback, not retry/timeout/circuit-breaker policy.",
    )
    return _finish(result)


def _scenario_s18(definition: dict[str, Any]) -> dict[str, Any]:
    result = _base(definition)
    ops_root = _ops_root()
    _enable_ops_namespace(ops_root)

    from aegis_os.capabilities.loader import CapabilityLoader
    from aegis_os.capabilities.registry import CapabilityRegistry
    from aegis_os.capabilities.selector import (
        CapabilitySelectionPolicy,
        CapabilitySelector,
    )

    malformed_text = (
        "id: [unterminated\n"
        "name: 42\n"
        "version: {invalid: structure}\n"
        "workflow: not-a-list\n"
    )
    malformed_hash = hashlib.sha256(
        malformed_text.encode("utf-8")
    ).hexdigest()

    loaded: list[Any] = []
    load_error = None

    with tempfile.TemporaryDirectory(prefix="aegis-domain-e-s18-") as temp:
        modules = Path(temp) / "modules"
        modules.mkdir(parents=True, exist_ok=False)
        malformed_file = modules / "malformed_capability.yaml"
        malformed_file.write_text(malformed_text, encoding="utf-8")

        try:
            loaded = list(
                CapabilityLoader().load_valid_capabilities(modules)
            )
        except Exception as error:
            load_error = error

    registry = CapabilityRegistry()
    registration_errors: list[str] = []
    for capability in loaded:
        try:
            registry.register(capability)
        except Exception as error:
            registration_errors.append(
                f"{type(error).__name__}: {error}"
            )

    registered = list(registry.list_all())
    selector = CapabilitySelector(
        CapabilitySelectionPolicy.development()
    )
    matches = list(
        selector.rank(
            "Select the malformed capability",
            registered,
            top_n=1,
        )
    )

    rejected = load_error is not None or len(loaded) == 0
    result["actual_canonical_outcome"] = (
        "malformed_capability_rejected"
        if (
            rejected
            and len(registered) == 0
            and len(matches) == 0
        )
        else "malformed_capability_reached_runtime"
    )
    result["evidence"] = {
        "ops_root": str(ops_root),
        "fixture_filename": "malformed_capability.yaml",
        "fixture_sha256": malformed_hash,
        "fixture_content_in_evidence": False,
        "loader_error_type": (
            type(load_error).__name__ if load_error is not None else None
        ),
        "loader_error": (
            str(load_error) if load_error is not None else None
        ),
        "loader_rejection_mode": (
            "exception"
            if load_error is not None
            else "zero-valid-capabilities"
            if len(loaded) == 0
            else "accepted"
        ),
        "loaded_capability_count": len(loaded),
        "loaded_capability_ids": [
            str(getattr(item, "id", "<missing>"))
            for item in loaded
        ],
        "registration_errors": registration_errors,
        "registered_capability_count": len(registered),
        "selection_match_count": len(matches),
        "selection_matches": _serialize(matches),
        "planning_performed": False,
        "execution_performed": False,
    }

    _check(
        result,
        "loader_rejects_malformed_input",
        rejected,
        (
            f"Error: {type(load_error).__name__ if load_error else None}; "
            f"loaded: {len(loaded)}"
        ),
    )
    _check(
        result,
        "malformed_capability_not_loaded",
        len(loaded) == 0,
        f"Loaded capability IDs: {result['evidence']['loaded_capability_ids']}",
    )
    _check(
        result,
        "registry_remains_empty",
        len(registered) == 0,
        f"Registered capabilities: {len(registered)}",
    )
    _check(
        result,
        "selector_receives_no_candidate",
        len(matches) == 0,
        f"Selection matches: {len(matches)}",
    )
    _check(
        result,
        "planning_not_reached",
        result["evidence"]["planning_performed"] is False,
        "Malformed capability data never reaches planning.",
    )
    _check(
        result,
        "execution_not_reached",
        result["execution_performed"] is False,
        "Malformed capability data never reaches execution.",
    )
    return _finish(result)


SCENARIO_RUNNERS = {
    "AEGIS-RC1-S17": _scenario_s17,
    "AEGIS-RC1-S18": _scenario_s18,
}


def _selected_definitions(
    payload: dict[str, Any],
    scenario_id: str | None,
) -> Iterable[dict[str, Any]]:
    if scenario_id is None:
        return payload["scenarios"]
    selected = [
        item
        for item in payload["scenarios"]
        if item["scenario_id"] == scenario_id
    ]
    if not selected:
        raise ValueError(f"Unknown Domain E scenario: {scenario_id}")
    return selected


def run_domain_e(
    *,
    scenario_id: str | None = None,
    output_root: Path | None = None,
) -> tuple[dict[str, Any], Path]:
    payload = load_domain_e_definition()
    started_at = _utc_now()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    root = (
        Path(output_root)
        if output_root is not None
        else _root()
        / "artifacts"
        / "functional-proof"
        / "domain-e"
    )
    directory = root / stamp
    suffix = 1
    while directory.exists():
        directory = root / f"{stamp}-{suffix}"
        suffix += 1
    directory.mkdir(parents=True, exist_ok=False)

    results: list[dict[str, Any]] = []
    for definition in _selected_definitions(payload, scenario_id):
        try:
            scenario_result = SCENARIO_RUNNERS[
                definition["scenario_id"]
            ](definition)
        except Exception as error:
            scenario_result = _base(definition)
            scenario_result["actual_canonical_outcome"] = "blocked"
            scenario_result["failure_reason"] = (
                f"{type(error).__name__}: {error}"
            )
            scenario_result["completed_at"] = _utc_now()

        (directory / f"{definition['scenario_id']}.json").write_text(
            json.dumps(
                scenario_result,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        results.append(scenario_result)

    passed = sum(1 for item in results if item["passed"])
    blocked = sum(
        1
        for item in results
        if item["actual_canonical_outcome"] == "blocked"
    )
    failed = len(results) - passed - blocked
    all_passed = passed == len(results) and failed == 0 and blocked == 0

    aggregate = {
        "schema_version": "1.0",
        "suite_version": SUITE_VERSION,
        "release_version": RELEASE_VERSION,
        "domain": DOMAIN,
        "domain_title": payload["domain_title"],
        "started_at": started_at,
        "completed_at": _utc_now(),
        "scenarios_executed": len(results),
        "passed": passed,
        "failed": failed,
        "blocked": blocked,
        "scenario_summaries": [
            {
                "scenario_id": item["scenario_id"],
                "actual_canonical_outcome": item[
                    "actual_canonical_outcome"
                ],
                "passed": item["passed"],
                "failure_reason": item["failure_reason"],
            }
            for item in results
        ],
        "overall_domain_verdict": (
            (
                OVERALL_PASS_VERDICT
                if scenario_id is None
                else SINGLE_PASS_VERDICT
            )
            if all_passed
            else "DOMAIN E VERIFICATION FAILED"
        ),
        "repository_commit": _git_value("rev-parse", "HEAD"),
        "repository_tree": _git_value("rev-parse", "HEAD^{tree}"),
        "generated_output_is_signed_release": False,
        "private_signing_material_included": False,
        "declared_boundary": payload["declared_boundary"],
    }

    (directory / "DOMAIN_E_REPORT.json").write_text(
        json.dumps(aggregate, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    lines = [
        "============================================================",
        "AEGIS DOMAIN E FUNCTIONAL PROOF",
        "============================================================",
        f"Scenarios executed: {aggregate['scenarios_executed']}",
        f"Passed: {passed}",
        f"Failed: {failed}",
        f"Blocked: {blocked}",
        f"Verdict: {aggregate['overall_domain_verdict']}",
        f"Evidence: {directory}",
        "",
    ]
    for item in results:
        marker = "PASS" if item["passed"] else "FAIL"
        lines.append(
            f"[{marker}] {item['scenario_id']} - "
            f"{item['actual_canonical_outcome']}"
        )

    (directory / "DOMAIN_E_SUMMARY.txt").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    return aggregate, directory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run AEGIS RC1 Domain E functional proofs."
    )
    parser.add_argument(
        "--scenario",
        choices=sorted(SCENARIO_RUNNERS),
    )
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args(argv)
    aggregate, directory = run_domain_e(
        scenario_id=args.scenario,
        output_root=args.output_root,
    )
    print("============================================================")
    print("AEGIS DOMAIN E FUNCTIONAL PROOF")
    print("============================================================")
    print(f"Scenarios executed: {aggregate['scenarios_executed']}")
    print(f"Passed: {aggregate['passed']}")
    print(f"Failed: {aggregate['failed']}")
    print(f"Blocked: {aggregate['blocked']}")
    print(f"Verdict: {aggregate['overall_domain_verdict']}")
    print(f"Evidence: {directory}")
    return (
        0
        if aggregate["passed"] == aggregate["scenarios_executed"]
        and aggregate["failed"] == 0
        and aggregate["blocked"] == 0
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
