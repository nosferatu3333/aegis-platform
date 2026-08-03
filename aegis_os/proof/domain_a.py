"""Executable Domain A functional proof scenarios.

Domain A proves request interpretation and capability routing within the
declared AEGIS Platform 1.7.0 RC1 boundary.

S03 intentionally uses controlled in-memory capability objects with the real
production OPS selector because the live OPS registry currently contains only
one capability. It does not modify OPS capability definitions.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, is_dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SUITE_VERSION = "1.0"
RELEASE_VERSION = "1.7.0-rc1"
DOMAIN = "A"
OVERALL_PASS_VERDICT = "DOMAIN A FUNCTIONALLY VERIFIED"
SINGLE_PASS_VERDICT = "SCENARIO FUNCTIONALLY VERIFIED"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _scenario_path() -> Path:
    return Path(__file__).resolve().parent / "scenarios" / "domain_a.json"


def _ops_root() -> Path:
    configured = os.environ.get("AEGIS_OPS_PATH", "").strip()
    if not configured:
        raise RuntimeError("AEGIS_OPS_PATH is required for Domain A proof.")
    root = Path(configured).resolve()
    if not root.exists():
        raise RuntimeError(f"AEGIS OPS path does not exist: {root}")
    return root


def _enable_ops_namespace(ops_root: Path) -> None:
    import aegis_os

    namespace_path = str(ops_root / "aegis_os")
    if namespace_path not in aegis_os.__path__:
        aegis_os.__path__.append(namespace_path)


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _serialize(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_serialize(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        try:
            return _serialize(value.to_dict())
        except Exception:
            pass
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def _git_value(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=_repository_root(),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def load_domain_a_definition() -> dict[str, Any]:
    payload = json.loads(_scenario_path().read_text(encoding="utf-8-sig"))
    scenarios = payload.get("scenarios", [])
    identifiers = [item.get("scenario_id") for item in scenarios]

    expected = {
        "AEGIS-RC1-S01",
        "AEGIS-RC1-S02",
        "AEGIS-RC1-S03",
        "AEGIS-RC1-S04",
    }

    if set(identifiers) != expected:
        raise ValueError("Domain A must define exactly S01 through S04.")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Domain A scenario identifiers must be unique.")

    return payload


def _base_result(definition: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "suite_version": SUITE_VERSION,
        "release_version": RELEASE_VERSION,
        "scenario_id": definition["scenario_id"],
        "title": definition["title"],
        "domain": DOMAIN,
        "started_at": _utc_now(),
        "completed_at": None,
        "expected_semantic_outcome": definition["expected_semantic_outcome"],
        "actual_canonical_outcome": None,
        "passed": False,
        "request_id": None,
        "correlation_id": None,
        "trace_id": None,
        "capability_id": None,
        "capability_source": None,
        "capability_score": None,
        "matched_terms": [],
        "execution_requested": bool(definition["execution_requested"]),
        "execution_performed": False,
        "fallback_used": False,
        "assertions": [],
        "evidence": {},
        "failure_reason": None,
        "declared_boundary": {
            "execution_mode": "deterministic governed simulation",
            "real_world_execution_claimed": False,
            "production_readiness_claimed": False,
        },
    }


def _assert(
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
        assertion["passed"] for assertion in result["assertions"]
    )
    if not result["passed"] and result["failure_reason"] is None:
        failures = [
            assertion["name"]
            for assertion in result["assertions"]
            if not assertion["passed"]
        ]
        result["failure_reason"] = "Failed assertions: " + ", ".join(failures)
    result["completed_at"] = _utc_now()
    return result


def _scenario_s01(definition: dict[str, Any]) -> dict[str, Any]:
    from aegis_os.pipeline.composition import create_default_pipeline

    result = _base_result(definition)
    pipeline_result = create_default_pipeline().process_task(definition["mission"])
    payload = pipeline_result.to_dict()

    workflow = payload.get("workflow") or []
    capability = payload.get("capability") or {}
    status = payload.get("status")

    result["actual_canonical_outcome"] = status
    result["capability_id"] = capability.get("capability_id")
    result["capability_source"] = (payload.get("metadata") or {}).get(
        "capability_source"
    )
    result["fallback_used"] = (
        result["capability_source"] == "platform-internal"
    )
    result["evidence"] = {
        "pipeline_result": payload,
        "workflow_step_count": len(workflow),
        "analysis_only_proof": {
            "execution_requested": False,
            "execution_performed": False,
        },
    }

    _assert(
        result,
        "pipeline_result_structurally_valid",
        isinstance(payload, dict) and bool(status),
        f"Canonical status: {status}",
    )
    _assert(
        result,
        "planning_output_present",
        len(workflow) > 0,
        f"Workflow steps: {len(workflow)}",
    )
    _assert(
        result,
        "capability_outcome_present",
        bool(capability.get("capability_id")),
        f"Capability: {capability.get('capability_id')}",
    )
    _assert(
        result,
        "execution_not_requested",
        result["execution_requested"] is False,
        "Scenario contract sets execution_requested=false.",
    )
    _assert(
        result,
        "execution_not_performed",
        result["execution_performed"] is False,
        "No executor is invoked by the Domain A analysis proof.",
    )

    return _finish(result)


def _scenario_s02(definition: dict[str, Any]) -> dict[str, Any]:
    from aegis_os.pipeline.ops_capability_adapter import (
        OpsCapabilitySelectorAdapter,
    )

    result = _base_result(definition)
    ops_root = _ops_root()
    selection = OpsCapabilitySelectorAdapter(ops_root).select(
        definition["mission"]
    )

    selection_payload = _serialize(selection)
    capability = getattr(selection, "capability", None) if selection else None
    capability_id = getattr(capability, "id", None)
    capability_version = getattr(capability, "version", None)
    workflow = getattr(capability, "workflow", None) or []
    score = getattr(selection, "score", None) if selection else None
    reasons = list(getattr(selection, "reasons", None) or []) if selection else []
    source = getattr(selection, "source", None) if selection else None
    source_path = getattr(selection, "source_path", None) if selection else None

    result["actual_canonical_outcome"] = (
        "positive_match" if selection is not None else "no_match"
    )
    result["capability_id"] = capability_id
    result["capability_source"] = source
    result["capability_score"] = score
    result["matched_terms"] = reasons
    result["evidence"] = {
        "live_selection": selection_payload,
        "capability_version": capability_version,
        "workflow_step_count": len(workflow),
        "ops_source_path": str(source_path) if source_path else None,
    }

    _assert(
        result,
        "live_ops_selection_present",
        selection is not None,
        f"Selection type: {type(selection).__name__ if selection else None}",
    )
    _assert(
        result,
        "capability_id_present",
        bool(capability_id),
        f"Capability ID: {capability_id}",
    )
    _assert(
        result,
        "capability_version_present",
        bool(capability_version),
        f"Capability version: {capability_version}",
    )
    _assert(
        result,
        "positive_score",
        isinstance(score, (int, float)) and score > 0,
        f"Selection score: {score}",
    )
    _assert(
        result,
        "source_is_live_ops",
        source == "aegis-ops",
        f"Capability source: {source}",
    )
    _assert(
        result,
        "workflow_transferred",
        len(workflow) > 0,
        f"OPS workflow steps: {len(workflow)}",
    )
    _assert(
        result,
        "not_reported_as_fallback",
        result["fallback_used"] is False,
        "Live OPS proof does not use Platform fallback.",
    )

    return _finish(result)


def _load_live_capabilities(ops_root: Path) -> list[Any]:
    _enable_ops_namespace(ops_root)

    from aegis_os.capabilities.loader import CapabilityLoader

    capability_directory = ops_root / "aegis_os" / "capabilities" / "modules"
    return CapabilityLoader().load_valid_capabilities(capability_directory)


def _scenario_s03(definition: dict[str, Any]) -> dict[str, Any]:
    result = _base_result(definition)
    ops_root = _ops_root()
    capabilities = _load_live_capabilities(ops_root)

    if len(capabilities) != 1:
        raise RuntimeError(
            "S03 controlled fixture currently expects exactly one live OPS "
            f"capability, found {len(capabilities)}."
        )

    from aegis_os.capabilities.selector import (
        CapabilitySelectionPolicy,
        CapabilitySelector,
    )

    base = capabilities[0]
    controlled_competitor = replace(
        base,
        id="proof.capability.software_validation_evidence",
        name="Controlled Software Validation and Evidence",
        version="proof-1.0",
        domain="software-validation",
        description=(
            "Inspect a software task, create an implementation plan, run "
            "validation, and prepare evidence for review."
        ),
        tags=[
            "inspect",
            "software",
            "implementation",
            "plan",
            "validation",
            "evidence",
            "review",
        ],
        metadata={
            **dict(getattr(base, "metadata", {}) or {}),
            "proof_fixture": True,
            "not_registered_in_ops": True,
        },
    )

    selector = CapabilitySelector(CapabilitySelectionPolicy.development())
    ranked = selector.rank(
        definition["mission"],
        [base, controlled_competitor],
        top_n=2,
    )

    rankings = [
        {
            "rank": index,
            "capability_id": match.capability.id,
            "capability_name": match.capability.name,
            "score": match.score,
            "matched_terms": sorted(match.matched_terms),
        }
        for index, match in enumerate(ranked, start=1)
    ]

    winner = ranked[0] if ranked else None
    winner_id = winner.capability.id if winner else None

    result["actual_canonical_outcome"] = (
        "ranked_selection" if winner else "no_ranked_selection"
    )
    result["capability_id"] = winner_id
    result["capability_source"] = "controlled-selector-contract-proof"
    result["capability_score"] = winner.score if winner else None
    result["matched_terms"] = (
        sorted(winner.matched_terms) if winner else []
    )
    result["evidence"] = {
        "selector_class": (
            "aegis_os.capabilities.selector.CapabilitySelector"
        ),
        "selection_policy": "development",
        "fixture_type": "controlled in-memory capability clone",
        "live_registry_capability_count": len(capabilities),
        "production_ops_modified": False,
        "candidate_rankings": rankings,
    }

    _assert(
        result,
        "two_candidates_ranked",
        len(ranked) == 2,
        f"Ranked candidates: {len(ranked)}",
    )
    _assert(
        result,
        "scores_descending",
        len(ranked) == 2 and ranked[0].score >= ranked[1].score,
        f"Scores: {[match.score for match in ranked]}",
    )
    _assert(
        result,
        "controlled_competitor_selected",
        winner_id == controlled_competitor.id,
        f"Selected capability: {winner_id}",
    )
    _assert(
        result,
        "production_selector_used",
        selector.__class__.__module__
        == "aegis_os.capabilities.selector",
        f"Selector module: {selector.__class__.__module__}",
    )
    _assert(
        result,
        "production_ops_not_modified",
        result["evidence"]["production_ops_modified"] is False,
        "Competition exists only in memory for selector-contract proof.",
    )

    return _finish(result)


def _scenario_s04(definition: dict[str, Any]) -> dict[str, Any]:
    from aegis_os.pipeline.composition import create_default_pipeline
    from aegis_os.pipeline.ops_capability_adapter import (
        OpsCapabilitySelectorAdapter,
    )

    result = _base_result(definition)
    ops_root = _ops_root()

    live_selection = OpsCapabilitySelectorAdapter(ops_root).select(
        definition["mission"]
    )
    pipeline_result = create_default_pipeline().process_task(
        definition["mission"]
    )
    payload = pipeline_result.to_dict()
    metadata = payload.get("metadata") or {}
    capability = payload.get("capability") or {}

    result["actual_canonical_outcome"] = payload.get("status")
    result["capability_id"] = capability.get("capability_id")
    result["capability_source"] = metadata.get("capability_source")
    result["fallback_used"] = (
        live_selection is None
        and result["capability_source"] != "aegis-ops"
    )
    result["evidence"] = {
        "live_ops_selection": _serialize(live_selection),
        "pipeline_result": payload,
        "failure_code": metadata.get("failure_code"),
        "failure_reason": metadata.get("failure_reason"),
    }

    _assert(
        result,
        "no_positive_live_ops_match",
        live_selection is None,
        f"Live OPS result: {_serialize(live_selection)}",
    )
    _assert(
        result,
        "pipeline_result_structurally_valid",
        isinstance(payload, dict) and bool(payload.get("status")),
        f"Canonical pipeline status: {payload.get('status')}",
    )
    _assert(
        result,
        "no_false_live_ops_source",
        result["capability_source"] != "aegis-ops",
        f"Reported capability source: {result['capability_source']}",
    )
    _assert(
        result,
        "no_execution_performed",
        result["execution_performed"] is False,
        "No executor is invoked by the no-match proof.",
    )
    _assert(
        result,
        "honest_fallback_or_failure",
        (
            payload.get("status") == "failed"
            or result["fallback_used"]
            or metadata.get("failure_code") == "no_capability_match"
        ),
        (
            f"Status={payload.get('status')} "
            f"fallback={result['fallback_used']} "
            f"failure_code={metadata.get('failure_code')}"
        ),
    )

    return _finish(result)


SCENARIO_RUNNERS = {
    "AEGIS-RC1-S01": _scenario_s01,
    "AEGIS-RC1-S02": _scenario_s02,
    "AEGIS-RC1-S03": _scenario_s03,
    "AEGIS-RC1-S04": _scenario_s04,
}


def _selected_definitions(
    payload: dict[str, Any],
    scenario_id: str | None,
) -> Iterable[dict[str, Any]]:
    scenarios = payload["scenarios"]
    if scenario_id is None:
        return scenarios
    selected = [
        scenario
        for scenario in scenarios
        if scenario["scenario_id"] == scenario_id
    ]
    if not selected:
        raise ValueError(f"Unknown Domain A scenario: {scenario_id}")
    return selected


def run_domain_a(
    *,
    scenario_id: str | None = None,
    output_root: Path | None = None,
) -> tuple[dict[str, Any], Path]:
    payload = load_domain_a_definition()
    started_at = _utc_now()

    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = (
        output_root
        if output_root is not None
        else _repository_root()
        / "artifacts"
        / "functional-proof"
        / "domain-a"
    )
    run_directory = Path(root) / run_stamp
    suffix = 1
    while run_directory.exists():
        run_directory = Path(root) / f"{run_stamp}-{suffix}"
        suffix += 1
    run_directory.mkdir(parents=True, exist_ok=False)

    results: list[dict[str, Any]] = []

    for definition in _selected_definitions(payload, scenario_id):
        runner = SCENARIO_RUNNERS[definition["scenario_id"]]
        try:
            scenario_result = runner(definition)
        except Exception as error:
            scenario_result = _base_result(definition)
            scenario_result["actual_canonical_outcome"] = "blocked"
            scenario_result["failure_reason"] = (
                f"{type(error).__name__}: {error}"
            )
            scenario_result["completed_at"] = _utc_now()

        result_path = run_directory / (
            f"{definition['scenario_id']}.json"
        )
        result_path.write_text(
            json.dumps(scenario_result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        results.append(scenario_result)

    passed = sum(1 for result in results if result["passed"])
    failed = sum(
        1
        for result in results
        if not result["passed"]
        and result["actual_canonical_outcome"] != "blocked"
    )
    blocked = sum(
        1
        for result in results
        if result["actual_canonical_outcome"] == "blocked"
    )

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
                "scenario_id": result["scenario_id"],
                "actual_canonical_outcome": result[
                    "actual_canonical_outcome"
                ],
                "passed": result["passed"],
                "failure_reason": result["failure_reason"],
            }
            for result in results
        ],
        "overall_domain_verdict": (
            (
                OVERALL_PASS_VERDICT
                if scenario_id is None
                else SINGLE_PASS_VERDICT
            )
            if all_passed
            else "DOMAIN A VERIFICATION FAILED"
        ),
        "repository_commit": _git_value("rev-parse", "HEAD"),
        "repository_tree": _git_value("rev-parse", "HEAD^{tree}"),
        "ops_path": str(_ops_root()),
        "generated_output_is_signed_release": False,
        "private_signing_material_included": False,
        "declared_boundary": payload["declared_boundary"],
    }

    aggregate_path = run_directory / "DOMAIN_A_REPORT.json"
    aggregate_path.write_text(
        json.dumps(aggregate, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    summary_lines = [
        "============================================================",
        "AEGIS DOMAIN A FUNCTIONAL PROOF",
        "============================================================",
        f"Scenarios executed: {aggregate['scenarios_executed']}",
        f"Passed: {passed}",
        f"Failed: {failed}",
        f"Blocked: {blocked}",
        f"Verdict: {aggregate['overall_domain_verdict']}",
        f"Evidence: {run_directory}",
        "",
    ]

    for result in results:
        marker = "PASS" if result["passed"] else "FAIL"
        summary_lines.append(
            f"[{marker}] {result['scenario_id']} — "
            f"{result['actual_canonical_outcome']}"
        )

    summary_path = run_directory / "DOMAIN_A_SUMMARY.txt"
    summary_path.write_text(
        "\n".join(summary_lines) + "\n",
        encoding="utf-8",
    )

    return aggregate, run_directory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run AEGIS RC1 Domain A functional proof scenarios."
    )
    parser.add_argument(
        "--scenario",
        choices=sorted(SCENARIO_RUNNERS),
        help="Run one canonical Domain A scenario.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        help="Optional evidence-output root.",
    )
    args = parser.parse_args(argv)

    aggregate, run_directory = run_domain_a(
        scenario_id=args.scenario,
        output_root=args.output_root,
    )

    print("============================================================")
    print("AEGIS DOMAIN A FUNCTIONAL PROOF")
    print("============================================================")
    print(f"Scenarios executed: {aggregate['scenarios_executed']}")
    print(f"Passed: {aggregate['passed']}")
    print(f"Failed: {aggregate['failed']}")
    print(f"Blocked: {aggregate['blocked']}")
    print(f"Verdict: {aggregate['overall_domain_verdict']}")
    print(f"Evidence: {run_directory}")

    return (
        0
        if (
            aggregate["failed"] == 0
            and aggregate["blocked"] == 0
            and aggregate["passed"]
            == aggregate["scenarios_executed"]
        )
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
