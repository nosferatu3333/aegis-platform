"""Tests for AEGIS RC1 Domain E functional proof."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aegis_os.proof.domain_e import (
    OVERALL_PASS_VERDICT,
    SINGLE_PASS_VERDICT,
    load_domain_e_definition,
    run_domain_e,
)

EXPECTED_IDS = {
    "AEGIS-RC1-S17",
    "AEGIS-RC1-S18",
}


def _result(directory: Path, scenario_id: str) -> dict:
    return json.loads(
        (directory / f"{scenario_id}.json").read_text(encoding="utf-8")
    )


def test_definitions_are_complete_and_unique():
    payload = load_domain_e_definition()
    identifiers = [item["scenario_id"] for item in payload["scenarios"]]
    assert set(identifiers) == EXPECTED_IDS
    assert len(identifiers) == len(set(identifiers))


@pytest.mark.parametrize("scenario_id", sorted(EXPECTED_IDS))
def test_each_scenario_passes(scenario_id: str, tmp_path: Path):
    aggregate, directory = run_domain_e(
        scenario_id=scenario_id,
        output_root=tmp_path,
    )
    assert aggregate["scenarios_executed"] == 1
    assert aggregate["passed"] == 1
    assert aggregate["failed"] == 0
    assert aggregate["blocked"] == 0
    assert aggregate["overall_domain_verdict"] == SINGLE_PASS_VERDICT
    result = _result(directory, scenario_id)
    assert result["passed"] is True
    assert all(item["passed"] for item in result["assertions"])


def test_s17_reports_unavailable_ops_and_truthful_fallback(tmp_path: Path):
    _, directory = run_domain_e(
        scenario_id="AEGIS-RC1-S17",
        output_root=tmp_path,
    )
    result = _result(directory, "AEGIS-RC1-S17")
    evidence = result["evidence"]

    assert result["actual_canonical_outcome"] == "bounded_fallback"
    assert evidence["direct_error_type"] == "OpsIntegrationError"
    assert evidence["diagnostic"]["available"] is False
    assert evidence["direct_adapter_selection"] is None
    assert len(evidence["fallback_calls"]) == 1
    assert (
        evidence["analysis"]["metadata"]["capability_source"]
        == "platform-bounded-fallback"
    )
    assert evidence["live_ops_claimed"] is False
    assert result["execution_performed"] is False


def test_s18_rejects_malformed_capability_before_registry(tmp_path: Path):
    _, directory = run_domain_e(
        scenario_id="AEGIS-RC1-S18",
        output_root=tmp_path,
    )
    result = _result(directory, "AEGIS-RC1-S18")
    evidence = result["evidence"]

    assert (
        result["actual_canonical_outcome"]
        == "malformed_capability_rejected"
    )
    assert evidence["loader_rejection_mode"] in {
        "exception",
        "zero-valid-capabilities",
    }
    assert evidence["loaded_capability_count"] == 0
    assert evidence["registered_capability_count"] == 0
    assert evidence["selection_match_count"] == 0
    assert evidence["planning_performed"] is False
    assert evidence["execution_performed"] is False


def test_aggregate_report_passes(tmp_path: Path):
    aggregate, directory = run_domain_e(output_root=tmp_path)
    assert aggregate["scenarios_executed"] == 2
    assert aggregate["passed"] == 2
    assert aggregate["failed"] == 0
    assert aggregate["blocked"] == 0
    assert aggregate["overall_domain_verdict"] == OVERALL_PASS_VERDICT
    assert (directory / "DOMAIN_E_REPORT.json").exists()
    assert (directory / "DOMAIN_E_SUMMARY.txt").exists()


def test_generated_evidence_uses_no_private_material_names(tmp_path: Path):
    _, directory = run_domain_e(output_root=tmp_path)
    prohibited = [
        path
        for path in directory.rglob("*")
        if path.is_file()
        and any(
            token in path.name.lower()
            for token in ("private", "secret", "signing-key")
        )
    ]
    assert prohibited == []
