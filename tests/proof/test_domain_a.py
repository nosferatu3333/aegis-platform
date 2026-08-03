"""Tests for AEGIS RC1 Domain A functional proof."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aegis_os.proof.domain_a import (
    OVERALL_PASS_VERDICT,
    SINGLE_PASS_VERDICT,
    load_domain_a_definition,
    run_domain_a,
)


EXPECTED_IDS = {
    "AEGIS-RC1-S01",
    "AEGIS-RC1-S02",
    "AEGIS-RC1-S03",
    "AEGIS-RC1-S04",
}


def test_domain_a_definitions_are_complete_and_unique():
    payload = load_domain_a_definition()
    scenarios = payload["scenarios"]
    identifiers = [scenario["scenario_id"] for scenario in scenarios]

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

    for scenario in scenarios:
        assert required <= set(scenario)


@pytest.mark.parametrize("scenario_id", sorted(EXPECTED_IDS))
def test_each_domain_a_scenario_passes(
    scenario_id: str,
    tmp_path: Path,
):
    aggregate, run_directory = run_domain_a(
        scenario_id=scenario_id,
        output_root=tmp_path,
    )

    assert aggregate["scenarios_executed"] == 1
    assert aggregate["passed"] == 1
    assert aggregate["failed"] == 0
    assert aggregate["blocked"] == 0
    assert aggregate["overall_domain_verdict"] == SINGLE_PASS_VERDICT

    result_path = run_directory / f"{scenario_id}.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))

    assert result["passed"] is True
    assert result["execution_performed"] is False
    assert result["assertions"]
    assert all(assertion["passed"] for assertion in result["assertions"])


def test_s02_uses_live_ops(tmp_path: Path):
    _, run_directory = run_domain_a(
        scenario_id="AEGIS-RC1-S02",
        output_root=tmp_path,
    )
    result = json.loads(
        (run_directory / "AEGIS-RC1-S02.json").read_text(
            encoding="utf-8"
        )
    )

    assert result["capability_source"] == "aegis-ops"
    assert result["capability_id"] == (
        "aegis.capability.iterative_ai_development"
    )
    assert result["capability_score"] > 0
    assert result["fallback_used"] is False


def test_s03_uses_controlled_competition_without_ops_mutation(
    tmp_path: Path,
):
    _, run_directory = run_domain_a(
        scenario_id="AEGIS-RC1-S03",
        output_root=tmp_path,
    )
    result = json.loads(
        (run_directory / "AEGIS-RC1-S03.json").read_text(
            encoding="utf-8"
        )
    )
    evidence = result["evidence"]

    assert result["passed"] is True
    assert evidence["live_registry_capability_count"] == 1
    assert evidence["production_ops_modified"] is False
    assert len(evidence["candidate_rankings"]) == 2
    assert evidence["candidate_rankings"][0]["score"] >= (
        evidence["candidate_rankings"][1]["score"]
    )


def test_s04_rejects_false_positive_live_ops_match(tmp_path: Path):
    _, run_directory = run_domain_a(
        scenario_id="AEGIS-RC1-S04",
        output_root=tmp_path,
    )
    result = json.loads(
        (run_directory / "AEGIS-RC1-S04.json").read_text(
            encoding="utf-8"
        )
    )

    assert result["evidence"]["live_ops_selection"] is None
    assert result["capability_source"] != "aegis-ops"
    assert result["execution_performed"] is False


def test_domain_a_aggregate_report_passes(tmp_path: Path):
    aggregate, run_directory = run_domain_a(output_root=tmp_path)

    assert aggregate["scenarios_executed"] == 4
    assert aggregate["passed"] == 4
    assert aggregate["failed"] == 0
    assert aggregate["blocked"] == 0
    assert aggregate["overall_domain_verdict"] == OVERALL_PASS_VERDICT
    assert (run_directory / "DOMAIN_A_REPORT.json").exists()
    assert (run_directory / "DOMAIN_A_SUMMARY.txt").exists()


def test_generated_evidence_contains_no_private_key_names(tmp_path: Path):
    _, run_directory = run_domain_a(output_root=tmp_path)

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
