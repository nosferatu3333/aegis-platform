"""Tests for AEGIS RC1 Domain C functional proof."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aegis_os.proof.domain_c import (
    OVERALL_PASS_VERDICT,
    SINGLE_PASS_VERDICT,
    load_domain_c_definition,
    run_domain_c,
)

IDS = {
    "AEGIS-RC1-S08",
    "AEGIS-RC1-S09",
    "AEGIS-RC1-S10",
    "AEGIS-RC1-S11",
}


def _result(directory: Path, scenario_id: str) -> dict:
    return json.loads(
        (directory / f"{scenario_id}.json").read_text(encoding="utf-8")
    )


def test_definitions_are_complete_and_unique():
    payload = load_domain_c_definition()
    ids = [item["scenario_id"] for item in payload["scenarios"]]
    assert set(ids) == IDS
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("scenario_id", sorted(IDS))
def test_each_scenario_passes(scenario_id: str, tmp_path: Path):
    aggregate, directory = run_domain_c(
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


def test_s08_completes_only_with_full_scope_grant(tmp_path: Path):
    _, directory = run_domain_c(
        scenario_id="AEGIS-RC1-S08",
        output_root=tmp_path,
    )
    result = _result(directory, "AEGIS-RC1-S08")
    assert result["actual_canonical_outcome"] == "completed"
    assert result["evidence"]["authority"]["ready"] is True
    assert result["evidence"]["execution"]["status"] == "completed"
    assert result["evidence"]["validation"]["status"] == "passed"
    assert result["evidence"]["reconciliation"]["trace_complete"] is True


def test_s09_missing_approval_pauses(tmp_path: Path):
    _, directory = run_domain_c(
        scenario_id="AEGIS-RC1-S09",
        output_root=tmp_path,
    )
    result = _result(directory, "AEGIS-RC1-S09")
    assert result["actual_canonical_outcome"] == "paused"
    assert result["evidence"]["authority"]["paused"] is True
    assert result["evidence"]["execution"] is None


def test_s10_denial_overrides_grant(tmp_path: Path):
    _, directory = run_domain_c(
        scenario_id="AEGIS-RC1-S10",
        output_root=tmp_path,
    )
    result = _result(directory, "AEGIS-RC1-S10")
    assert result["actual_canonical_outcome"] == "denied"
    assert result["evidence"]["authority"]["denied"] is True
    assert any(
        item["outcome"] == "deny"
        for item in result["evidence"]["authority"]["decisions"]
    )


def test_s11_partial_scope_pauses(tmp_path: Path):
    _, directory = run_domain_c(
        scenario_id="AEGIS-RC1-S11",
        output_root=tmp_path,
    )
    result = _result(directory, "AEGIS-RC1-S11")
    assert result["actual_canonical_outcome"] == "paused"
    assert set(result["evidence"]["granted_scope"]) < set(
        result["evidence"]["required_scope"]
    )
    assert result["evidence"]["execution"] is None


def test_aggregate_report_passes(tmp_path: Path):
    aggregate, directory = run_domain_c(output_root=tmp_path)
    assert aggregate["scenarios_executed"] == 4
    assert aggregate["passed"] == 4
    assert aggregate["failed"] == 0
    assert aggregate["blocked"] == 0
    assert aggregate["overall_domain_verdict"] == OVERALL_PASS_VERDICT
    assert (directory / "DOMAIN_C_REPORT.json").exists()
    assert (directory / "DOMAIN_C_SUMMARY.txt").exists()


def test_generated_evidence_uses_no_private_material_names(tmp_path: Path):
    _, directory = run_domain_c(output_root=tmp_path)
    prohibited = [
        path
        for path in directory.rglob("*")
        if path.is_file()
        and any(token in path.name.lower() for token in ("private", "secret", "signing-key"))
    ]
    assert prohibited == []
