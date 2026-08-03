"""Tests for AEGIS RC1 Domain B functional proof."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aegis_os.proof.domain_b import (
    OVERALL_PASS_VERDICT,
    SINGLE_PASS_VERDICT,
    load_domain_b_definition,
    run_domain_b,
)

EXPECTED_IDS = {
    "AEGIS-RC1-S05",
    "AEGIS-RC1-S06",
    "AEGIS-RC1-S07",
}


def _load_result(run_directory: Path, scenario_id: str) -> dict:
    return json.loads(
        (run_directory / f"{scenario_id}.json").read_text(encoding="utf-8")
    )


def test_domain_b_definitions_are_complete_and_unique():
    payload = load_domain_b_definition()
    identifiers = [
        scenario["scenario_id"] for scenario in payload["scenarios"]
    ]
    assert set(identifiers) == EXPECTED_IDS
    assert len(identifiers) == len(set(identifiers))

    required = {
        "scenario_id",
        "title",
        "description",
        "mission",
        "execution_requested",
        "required_dependency_state",
        "expected_semantic_outcome",
        "expected_canonical_fields",
        "prohibited_outcomes",
        "evidence_requirements",
        "execution_method",
    }
    for scenario in payload["scenarios"]:
        assert required <= set(scenario)


@pytest.mark.parametrize("scenario_id", sorted(EXPECTED_IDS))
def test_each_domain_b_scenario_passes(
    scenario_id: str,
    tmp_path: Path,
):
    aggregate, run_directory = run_domain_b(
        scenario_id=scenario_id,
        output_root=tmp_path,
    )
    assert aggregate["scenarios_executed"] == 1
    assert aggregate["passed"] == 1
    assert aggregate["failed"] == 0
    assert aggregate["blocked"] == 0
    assert aggregate["overall_domain_verdict"] == SINGLE_PASS_VERDICT

    result = _load_result(run_directory, scenario_id)
    assert result["passed"] is True
    assert result["assertions"]
    assert all(assertion["passed"] for assertion in result["assertions"])


def test_s05_produces_finite_non_executing_plan(tmp_path: Path):
    _, run_directory = run_domain_b(
        scenario_id="AEGIS-RC1-S05",
        output_root=tmp_path,
    )
    result = _load_result(run_directory, "AEGIS-RC1-S05")
    evidence = result["evidence"]
    plan = evidence["canonical_plan"]

    assert result["passed"] is True
    assert evidence["actual_step_count"] == 3
    assert evidence["configured_max_steps"] == 4
    assert evidence["step_sequences"] == [1, 2, 3]
    assert plan["expected_evidence"]
    assert result["execution_requested"] is False
    assert result["execution_performed"] is False


def test_s06_rejects_expansion_through_real_bounds(tmp_path: Path):
    _, run_directory = run_domain_b(
        scenario_id="AEGIS-RC1-S06",
        output_root=tmp_path,
    )
    result = _load_result(run_directory, "AEGIS-RC1-S06")
    evidence = result["evidence"]

    assert result["passed"] is True
    assert (
        result["actual_canonical_outcome"]
        == "planning_bounds_rejected_expansion"
    )
    assert evidence["configured_max_steps"] == 3
    assert evidence["accepted_step_count"] == 3
    assert evidence["expanded_workflow_step_count"] == 4
    assert evidence["expanded_plan_emitted"] is False
    assert evidence["planning_error_type"] == "BoundedPlanningAdapterError"
    assert "maximum of 3" in evidence["planning_error"]
    assert evidence["semantic_scope_classifier_present"] is False
    assert result["execution_performed"] is False


def test_s07_produces_conformant_cancelled_receipt(tmp_path: Path):
    _, run_directory = run_domain_b(
        scenario_id="AEGIS-RC1-S07",
        output_root=tmp_path,
    )
    result = _load_result(run_directory, "AEGIS-RC1-S07")
    evidence = result["evidence"]
    receipt = evidence["execution_receipt"]
    validation = evidence["conformance"]

    assert result["passed"] is True
    assert result["actual_canonical_outcome"] == "cancelled"
    assert receipt["status"] == "cancelled"
    assert receipt["completed_steps"] == 1
    assert receipt["failed_steps"] == 0
    assert evidence["step_statuses"] == [
        "completed",
        "skipped",
        "skipped",
    ]
    assert validation["status"] == "passed"
    assert validation["operation_outcome"] == "cancelled"
    assert evidence["live_stop_request_hook_present"] is False


def test_domain_b_aggregate_report_passes(tmp_path: Path):
    aggregate, run_directory = run_domain_b(output_root=tmp_path)
    assert aggregate["scenarios_executed"] == 3
    assert aggregate["passed"] == 3
    assert aggregate["failed"] == 0
    assert aggregate["blocked"] == 0
    assert aggregate["overall_domain_verdict"] == OVERALL_PASS_VERDICT
    assert (run_directory / "DOMAIN_B_REPORT.json").exists()
    assert (run_directory / "DOMAIN_B_SUMMARY.txt").exists()


def test_generated_domain_b_evidence_has_no_private_names(tmp_path: Path):
    _, run_directory = run_domain_b(output_root=tmp_path)
    prohibited = [
        path
        for path in run_directory.rglob("*")
        if path.is_file()
        and any(
            token in path.name.lower()
            for token in ("private", "secret", "signing-key")
        )
    ]
    assert prohibited == []
