"""Tests for AEGIS RC1 Domain D functional proof."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aegis_os.proof.domain_d import (
    OVERALL_PASS_VERDICT,
    SINGLE_PASS_VERDICT,
    load_domain_d_definition,
    run_domain_d,
)

EXPECTED_IDS = {
    "AEGIS-RC1-S12",
    "AEGIS-RC1-S13",
    "AEGIS-RC1-S14",
    "AEGIS-RC1-S15",
    "AEGIS-RC1-S16",
}


def _result(directory: Path, scenario_id: str) -> dict:
    return json.loads(
        (directory / f"{scenario_id}.json").read_text(encoding="utf-8")
    )


def test_definitions_are_complete_and_unique():
    payload = load_domain_d_definition()
    identifiers = [item["scenario_id"] for item in payload["scenarios"]]
    assert set(identifiers) == EXPECTED_IDS
    assert len(identifiers) == len(set(identifiers))


@pytest.mark.parametrize("scenario_id", sorted(EXPECTED_IDS))
def test_each_scenario_passes(scenario_id: str, tmp_path: Path):
    aggregate, directory = run_domain_d(
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


def test_s12_completed_execution_creates_verified_evidence(tmp_path: Path):
    _, directory = run_domain_d(
        scenario_id="AEGIS-RC1-S12",
        output_root=tmp_path,
    )
    result = _result(directory, "AEGIS-RC1-S12")
    reconciliation = result["evidence"]["reconciliation"]
    assert result["actual_canonical_outcome"] == "complete"
    assert result["evidence"]["execution_receipt"]["status"] == "completed"
    assert result["evidence"]["conformance"]["status"] == "passed"
    assert reconciliation["completion_state"] == "complete"
    assert reconciliation["evidence_state"] == "verified"
    assert reconciliation["trace_complete"] is True


def test_s13_failed_execution_never_becomes_complete(tmp_path: Path):
    _, directory = run_domain_d(
        scenario_id="AEGIS-RC1-S13",
        output_root=tmp_path,
    )
    result = _result(directory, "AEGIS-RC1-S13")
    reconciliation = result["evidence"]["reconciliation"]
    assert result["actual_canonical_outcome"] == "failed"
    assert result["evidence"]["step_statuses"] == [
        "completed",
        "failed",
        "skipped",
    ]
    assert result["evidence"]["conformance"]["status"] == "passed"
    assert reconciliation["completion_state"] == "failed"
    assert reconciliation["step_result_statuses"] == [
        "succeeded",
        "failed",
        "skipped",
    ]


def test_s14_non_terminal_receipt_is_rejected(tmp_path: Path):
    _, directory = run_domain_d(
        scenario_id="AEGIS-RC1-S14",
        output_root=tmp_path,
    )
    result = _result(directory, "AEGIS-RC1-S14")
    evidence = result["evidence"]
    assert result["actual_canonical_outcome"] == "invalid_receipt_rejected"
    assert evidence["terminal_execution_valid"] is False
    assert evidence["reconciliation_emitted"] is False
    assert evidence["rejection_type"] == "ValueError"
    assert "terminal" in evidence["rejection_message"].lower()


def test_s15_provenance_hash_detects_controlled_mutation(tmp_path: Path):
    _, directory = run_domain_d(
        scenario_id="AEGIS-RC1-S15",
        output_root=tmp_path,
    )
    result = _result(directory, "AEGIS-RC1-S15")
    evidence = result["evidence"]
    assert (
        result["actual_canonical_outcome"]
        == "evidence_hash_mismatch_detected"
    )
    assert evidence["hash_matched_before_mutation"] is True
    assert evidence["hash_matched_after_mutation"] is False
    assert (
        evidence[
            "automatic_post_reconciliation_integrity_verifier_present"
        ]
        is False
    )


def test_s16_trace_links_every_evidence_record(tmp_path: Path):
    _, directory = run_domain_d(
        scenario_id="AEGIS-RC1-S16",
        output_root=tmp_path,
    )
    result = _result(directory, "AEGIS-RC1-S16")
    evidence = result["evidence"]
    reconciliation = evidence["reconciliation"]
    assert result["actual_canonical_outcome"] == "complete_trace"
    assert reconciliation["trace_complete"] is True
    assert evidence["relationships"].count("planned_from") == 1
    assert evidence["relationships"].count("resulted_in") == 1
    assert evidence["supported_by_count"] == reconciliation["evidence_count"]
    assert set(reconciliation["trace_evidence_ids"]) == set(
        reconciliation["evidence_ids"]
    )


def test_aggregate_report_passes(tmp_path: Path):
    aggregate, directory = run_domain_d(output_root=tmp_path)
    assert aggregate["scenarios_executed"] == 5
    assert aggregate["passed"] == 5
    assert aggregate["failed"] == 0
    assert aggregate["blocked"] == 0
    assert aggregate["overall_domain_verdict"] == OVERALL_PASS_VERDICT
    assert (directory / "DOMAIN_D_REPORT.json").exists()
    assert (directory / "DOMAIN_D_SUMMARY.txt").exists()


def test_generated_evidence_uses_no_private_material_names(tmp_path: Path):
    _, directory = run_domain_d(output_root=tmp_path)
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
