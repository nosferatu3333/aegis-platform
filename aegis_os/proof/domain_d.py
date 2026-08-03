"""Executable Domain D functional proof scenarios.

Domain D verifies the simulated execution, conformance, reconciliation,
evidence-provenance, and cognitive-trace contracts present in AEGIS Platform
1.7.0 RC1.

S15 performs a controlled digest comparison using the exact serialization and
SHA-256 method used by the production reconciler. RC1 records provenance hashes
but does not expose an automatic post-reconciliation integrity-verifier service.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

SUITE_VERSION = "1.0"
RELEASE_VERSION = "1.7.0-rc1"
DOMAIN = "D"
OVERALL_PASS_VERDICT = "DOMAIN D FUNCTIONALLY VERIFIED"
SINGLE_PASS_VERDICT = "SCENARIO FUNCTIONALLY VERIFIED"
NOW = datetime(2026, 8, 2, 23, 0, tzinfo=UTC)


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _definition_path() -> Path:
    return Path(__file__).resolve().parent / "scenarios" / "domain_d.json"


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


def load_domain_d_definition() -> dict[str, Any]:
    payload = json.loads(_definition_path().read_text(encoding="utf-8-sig"))
    identifiers = [item["scenario_id"] for item in payload["scenarios"]]
    expected = {
        "AEGIS-RC1-S12",
        "AEGIS-RC1-S13",
        "AEGIS-RC1-S14",
        "AEGIS-RC1-S15",
        "AEGIS-RC1-S16",
    }
    if set(identifiers) != expected:
        raise ValueError("Domain D must define exactly S12 through S16.")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Domain D scenario identifiers must be unique.")
    return payload


class _UnusedSelector:
    def select(self, task: str, **context: Any) -> Any:
        raise AssertionError("Domain D must consume a canonical selection.")


def _identifier_suffix(token: str) -> str:
    clean = token.strip()
    if len(clean) != 2 or not clean.isdigit():
        raise ValueError("Domain D scenario token must contain two digits.")
    return f"d{clean}{'0' * 13}"


def _selection(token: str):
    from aegis_core.contracts import (
        AuthorityRequirement,
        CapabilitySelection,
        EligibilityState,
        OperationalState,
    )

    suffix = _identifier_suffix(token)
    return CapabilitySelection(
        request_id=f"req_{suffix}",
        capability_id="cap_d000000000000001",
        capability_version="1.0.0",
        eligibility=EligibilityState.ELIGIBLE,
        rationale="Canonical Domain D execution and evidence capability.",
        health_state=OperationalState.HEALTHY,
        authority_requirement=AuthorityRequirement.NONE,
        selection_id=f"sel_{suffix}",
    )


def _analysis(token: str, workflow: list[str]):
    from aegis_os.pipeline.request_pipeline import CognitiveRequestPipeline

    return CognitiveRequestPipeline(
        capability_selector=_UnusedSelector()
    ).process_selection(
        task="Perform one bounded governed change",
        interpretation_id=f"int_{_identifier_suffix(token)}",
        selection=_selection(token),
        workflow_definition=workflow,
    )


def _execution_bundle(token: str, workflow: list[str]) -> dict[str, Any]:
    from aegis_os.execution.authority_adapter import AuthorityGatedExecutionAdapter
    from aegis_os.execution.conformance import ExecutionConformanceValidator
    from aegis_os.execution.execution_engine import ExecutionEngine
    from aegis_os.execution.reconciliation import ExecutionResultReconciler

    analysis = _analysis(token, workflow)
    plan = analysis.canonical_plan
    if plan is None:
        raise RuntimeError("Domain D analysis did not produce a canonical plan.")

    authority = AuthorityGatedExecutionAdapter().prepare(
        plan=plan,
        selected_agent=analysis.capability.name,
        capability_id=analysis.capability.capability_id,
    )
    if not authority.ready or authority.execution_request is None:
        raise RuntimeError("Authority-free Domain D plan did not become executable.")

    execution_request = authority.execution_request
    receipt = ExecutionEngine(clock=lambda: NOW).execute(execution_request)
    validation = ExecutionConformanceValidator().validate(
        request_id=plan.request_id,
        analysis=analysis,
        execution_request=execution_request,
        receipt=receipt,
    )
    reconciled = ExecutionResultReconciler(
        clock=lambda: NOW
    ).reconcile(receipt)

    return {
        "analysis": analysis,
        "plan": plan,
        "authority": authority,
        "execution_request": execution_request,
        "receipt": receipt,
        "validation": validation,
        "reconciled": reconciled,
    }


def _reconciliation_payload(reconciled) -> dict[str, Any]:
    return {
        "request_id": reconciled.request_id,
        "plan_id": reconciled.plan_id,
        "outcome": reconciled.outcome.value,
        "step_result_statuses": [
            item.status.value for item in reconciled.step_results
        ],
        "evidence_count": len(reconciled.evidence),
        "evidence_ids": [item.evidence_id for item in reconciled.evidence],
        "evidence_verification_states": [
            item.verification_state.value for item in reconciled.evidence
        ],
        "completion_state": reconciled.result.completion_state.value,
        "evidence_state": reconciled.result.evidence_state.value,
        "result_id": reconciled.result.result_id,
        "result_limitations": list(reconciled.result.limitations),
        "trace_id": reconciled.trace.trace_id,
        "trace_complete": reconciled.trace.is_complete_result_trace,
        "trace_evidence_ids": list(reconciled.trace.evidence_ids),
        "trace_links": [
            {
                "source_type": link.source_type,
                "source_id": link.source_id,
                "target_type": link.target_type,
                "target_id": link.target_id,
                "relationship": link.relationship.value,
            }
            for link in reconciled.trace.links
        ],
    }


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
        "declared_boundary": {
            "execution_mode": "deterministic governed simulation",
            "automatic_post_reconciliation_integrity_verifier_present": False,
            "external_effect_verification_present": False,
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
        failures = [
            item["name"]
            for item in result["assertions"]
            if not item["passed"]
        ]
        result["failure_reason"] = "Failed assertions: " + ", ".join(failures)
    result["completed_at"] = _utc_now()
    return result


def _scenario_s12(definition: dict[str, Any]) -> dict[str, Any]:
    from aegis_os.execution.conformance import ConformanceStatus
    from aegis_os.execution.models import ExecutionStatus
    from aegis_os.execution.reconciliation import ReconciliationOutcome

    result = _base(definition)
    bundle = _execution_bundle(
        "12",
        [
            "Execute controlled simulated work",
            "Record controlled execution evidence",
        ],
    )
    receipt = bundle["receipt"]
    validation = bundle["validation"]
    reconciled = bundle["reconciled"]

    result["actual_canonical_outcome"] = reconciled.outcome.value
    result["evidence"] = {
        "canonical_plan": bundle["plan"].to_dict(),
        "execution_request": bundle["execution_request"].to_dict(),
        "execution_receipt": receipt.to_dict(),
        "receipt_metadata": dict(receipt.metadata),
        "conformance": validation.to_dict(),
        "reconciliation": _reconciliation_payload(reconciled),
    }

    _check(
        result,
        "receipt_completed",
        receipt.status is ExecutionStatus.COMPLETED,
        f"Receipt status: {receipt.status.value}",
    )
    _check(
        result,
        "conformance_passed",
        validation.status is ConformanceStatus.PASSED,
        f"Conformance: {validation.status.value}",
    )
    _check(
        result,
        "reconciliation_complete",
        reconciled.outcome is ReconciliationOutcome.COMPLETE,
        f"Reconciliation: {reconciled.outcome.value}",
    )
    _check(
        result,
        "verified_evidence_created",
        len(reconciled.evidence) == len(receipt.steps) + 1
        and all(
            item.verification_state.value == "verified"
            for item in reconciled.evidence
        ),
        f"Evidence records: {len(reconciled.evidence)}",
    )
    _check(
        result,
        "simulation_limitation_preserved",
        any(
            "simulated" in item.lower()
            for item in reconciled.result.limitations
        ),
        f"Limitations: {list(reconciled.result.limitations)}",
    )
    _check(
        result,
        "trace_complete",
        reconciled.trace.is_complete_result_trace is True,
        f"Trace ID: {reconciled.trace.trace_id}",
    )
    return _finish(result)


def _scenario_s13(definition: dict[str, Any]) -> dict[str, Any]:
    from aegis_os.execution.conformance import ConformanceStatus
    from aegis_os.execution.models import (
        ExecutionStatus,
        ExecutionStepStatus,
    )
    from aegis_os.execution.reconciliation import ReconciliationOutcome

    result = _base(definition)
    bundle = _execution_bundle(
        "13",
        [
            "Complete controlled preparation",
            "[simulate-failure] Trigger controlled execution failure",
            "This step must be skipped",
        ],
    )
    receipt = bundle["receipt"]
    validation = bundle["validation"]
    reconciled = bundle["reconciled"]
    statuses = [item.status.value for item in receipt.steps]

    result["actual_canonical_outcome"] = reconciled.outcome.value
    result["evidence"] = {
        "canonical_plan": bundle["plan"].to_dict(),
        "execution_request": bundle["execution_request"].to_dict(),
        "execution_receipt": receipt.to_dict(),
        "receipt_metadata": dict(receipt.metadata),
        "conformance": validation.to_dict(),
        "reconciliation": _reconciliation_payload(reconciled),
        "step_statuses": statuses,
    }

    _check(
        result,
        "receipt_failed",
        receipt.status is ExecutionStatus.FAILED,
        f"Receipt status: {receipt.status.value}",
    )
    _check(
        result,
        "failure_shape_preserved",
        statuses
        == [
            ExecutionStepStatus.COMPLETED.value,
            ExecutionStepStatus.FAILED.value,
            ExecutionStepStatus.SKIPPED.value,
        ],
        f"Step statuses: {statuses}",
    )
    _check(
        result,
        "failed_receipt_conforms",
        validation.status is ConformanceStatus.PASSED,
        f"Conformance: {validation.status.value}",
    )
    _check(
        result,
        "reconciliation_remains_failed",
        reconciled.outcome is ReconciliationOutcome.FAILED
        and reconciled.result.completion_state.value == "failed",
        (
            f"Outcome: {reconciled.outcome.value}; completion: "
            f"{reconciled.result.completion_state.value}"
        ),
    )
    _check(
        result,
        "step_results_preserve_failure",
        [item.status.value for item in reconciled.step_results]
        == ["succeeded", "failed", "skipped"],
        str([item.status.value for item in reconciled.step_results]),
    )
    _check(
        result,
        "failure_evidence_created",
        len(reconciled.evidence) == len(receipt.steps) + 1
        and bool(reconciled.result.limitations),
        f"Evidence records: {len(reconciled.evidence)}",
    )
    return _finish(result)


def _scenario_s14(definition: dict[str, Any]) -> dict[str, Any]:
    from aegis_os.execution.conformance import terminal_execution_is_valid
    from aegis_os.execution.execution_engine import ExecutionEngine
    from aegis_os.execution.models import ExecutionStatus
    from aegis_os.execution.reconciliation import ExecutionResultReconciler

    result = _base(definition)
    analysis = _analysis(
        "14",
        ["Execute controlled work", "Record controlled evidence"],
    )
    plan = analysis.canonical_plan
    if plan is None:
        raise RuntimeError("S14 lacks a canonical plan.")

    from aegis_os.execution.authority_adapter import AuthorityGatedExecutionAdapter

    prepared = AuthorityGatedExecutionAdapter().prepare(
        plan=plan,
        selected_agent=analysis.capability.name,
        capability_id=analysis.capability.capability_id,
    )
    if prepared.execution_request is None:
        raise RuntimeError("S14 execution request was not prepared.")

    receipt = ExecutionEngine(clock=lambda: NOW).execute(
        prepared.execution_request
    )
    receipt.status = ExecutionStatus.RUNNING

    reconciliation = None
    rejection = None
    try:
        reconciliation = ExecutionResultReconciler(
            clock=lambda: NOW
        ).reconcile(receipt)
    except ValueError as error:
        rejection = error

    result["actual_canonical_outcome"] = (
        "invalid_receipt_rejected"
        if rejection is not None
        else "invalid_receipt_accepted"
    )
    result["evidence"] = {
        "invalid_receipt": receipt.to_dict(),
        "receipt_metadata": dict(receipt.metadata),
        "terminal_execution_valid": terminal_execution_is_valid(receipt),
        "reconciliation_emitted": reconciliation is not None,
        "rejection_type": (
            type(rejection).__name__ if rejection is not None else None
        ),
        "rejection_message": (
            str(rejection) if rejection is not None else None
        ),
    }

    _check(
        result,
        "receipt_is_non_terminal",
        receipt.status is ExecutionStatus.RUNNING,
        f"Receipt status: {receipt.status.value}",
    )
    _check(
        result,
        "terminal_contract_rejects_receipt",
        terminal_execution_is_valid(receipt) is False,
        "Non-terminal receipt must fail terminal execution validation.",
    )
    _check(
        result,
        "reconciler_rejects_invalid_receipt",
        rejection is not None and "terminal" in str(rejection).lower(),
        f"Rejection: {rejection}",
    )
    _check(
        result,
        "no_reconciled_result_emitted",
        reconciliation is None,
        f"Reconciliation emitted: {reconciliation is not None}",
    )
    return _finish(result)


def _receipt_digest(receipt) -> str:
    payload = json.dumps(
        receipt.to_dict(),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _scenario_s15(definition: dict[str, Any]) -> dict[str, Any]:
    result = _base(definition)
    bundle = _execution_bundle(
        "15",
        ["Execute controlled work", "Record controlled evidence"],
    )
    receipt = bundle["receipt"]
    reconciled = bundle["reconciled"]

    receipt_evidence = next(
        item
        for item in reconciled.evidence
        if item.subject_type == "execution_receipt"
    )
    stored_digest = receipt_evidence.provenance[0].content_hash
    original_digest = _receipt_digest(receipt)

    receipt.steps[0].outputs["message"] = (
        "Controlled post-reconciliation mutation."
    )
    mutated_digest = _receipt_digest(receipt)

    result["actual_canonical_outcome"] = (
        "evidence_hash_mismatch_detected"
        if stored_digest == original_digest
        and stored_digest != mutated_digest
        else "evidence_hash_mismatch_not_detected"
    )
    result["evidence"] = {
        "comparison_mode": (
            "controlled recomputation using production receipt "
            "serialization and SHA-256"
        ),
        "automatic_post_reconciliation_integrity_verifier_present": False,
        "receipt_evidence_id": receipt_evidence.evidence_id,
        "stored_provenance_hash": stored_digest,
        "original_receipt_hash": original_digest,
        "mutated_receipt_hash": mutated_digest,
        "hash_matched_before_mutation": stored_digest == original_digest,
        "hash_matched_after_mutation": stored_digest == mutated_digest,
        "mutated_receipt": receipt.to_dict(),
    }

    _check(
        result,
        "production_hash_matches_original",
        stored_digest == original_digest,
        f"Stored: {stored_digest}; original: {original_digest}",
    )
    _check(
        result,
        "mutation_changes_digest",
        original_digest != mutated_digest,
        f"Original: {original_digest}; mutated: {mutated_digest}",
    )
    _check(
        result,
        "stored_evidence_detects_mismatch",
        stored_digest != mutated_digest,
        f"Stored: {stored_digest}; mutated: {mutated_digest}",
    )
    _check(
        result,
        "automatic_verifier_not_claimed",
        result["evidence"][
            "automatic_post_reconciliation_integrity_verifier_present"
        ]
        is False,
        "RC1 records provenance hashes but has no automatic verifier service.",
    )
    return _finish(result)


def _scenario_s16(definition: dict[str, Any]) -> dict[str, Any]:
    result = _base(definition)
    bundle = _execution_bundle(
        "16",
        ["Execute controlled work", "Record controlled evidence"],
    )
    plan = bundle["plan"]
    reconciled = bundle["reconciled"]
    links = reconciled.trace.links
    relationships = [item.relationship.value for item in links]
    supported_links = [
        item for item in links if item.relationship.value == "supported_by"
    ]

    result["actual_canonical_outcome"] = (
        "complete_trace"
        if reconciled.trace.is_complete_result_trace
        else "incomplete_trace"
    )
    result["evidence"] = {
        "canonical_plan": plan.to_dict(),
        "reconciliation": _reconciliation_payload(reconciled),
        "relationships": relationships,
        "supported_by_count": len(supported_links),
    }

    _check(
        result,
        "trace_contract_complete",
        reconciled.trace.is_complete_result_trace is True,
        f"Trace ID: {reconciled.trace.trace_id}",
    )
    _check(
        result,
        "request_identity_preserved",
        reconciled.trace.request_id == reconciled.request_id,
        (
            f"Trace request: {reconciled.trace.request_id}; "
            f"reconciled request: {reconciled.request_id}"
        ),
    )
    _check(
        result,
        "plan_identity_preserved",
        reconciled.trace.plan_id == plan.plan_id == reconciled.plan_id,
        (
            f"Trace plan: {reconciled.trace.plan_id}; "
            f"plan: {plan.plan_id}"
        ),
    )
    _check(
        result,
        "request_to_plan_link_present",
        relationships.count("planned_from") == 1,
        f"Relationships: {relationships}",
    )
    _check(
        result,
        "plan_to_result_link_present",
        relationships.count("resulted_in") == 1,
        f"Relationships: {relationships}",
    )
    _check(
        result,
        "all_evidence_linked",
        len(supported_links) == len(reconciled.evidence)
        and set(reconciled.trace.evidence_ids)
        == {item.evidence_id for item in reconciled.evidence},
        (
            f"Supported links: {len(supported_links)}; "
            f"evidence: {len(reconciled.evidence)}"
        ),
    )
    return _finish(result)


SCENARIO_RUNNERS = {
    "AEGIS-RC1-S12": _scenario_s12,
    "AEGIS-RC1-S13": _scenario_s13,
    "AEGIS-RC1-S14": _scenario_s14,
    "AEGIS-RC1-S15": _scenario_s15,
    "AEGIS-RC1-S16": _scenario_s16,
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
        raise ValueError(f"Unknown Domain D scenario: {scenario_id}")
    return selected


def run_domain_d(
    *,
    scenario_id: str | None = None,
    output_root: Path | None = None,
) -> tuple[dict[str, Any], Path]:
    payload = load_domain_d_definition()
    started_at = _utc_now()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    root = (
        Path(output_root)
        if output_root is not None
        else _root()
        / "artifacts"
        / "functional-proof"
        / "domain-d"
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
            else "DOMAIN D VERIFICATION FAILED"
        ),
        "repository_commit": _git_value("rev-parse", "HEAD"),
        "repository_tree": _git_value("rev-parse", "HEAD^{tree}"),
        "generated_output_is_signed_release": False,
        "private_signing_material_included": False,
        "declared_boundary": payload["declared_boundary"],
    }

    (directory / "DOMAIN_D_REPORT.json").write_text(
        json.dumps(aggregate, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    lines = [
        "============================================================",
        "AEGIS DOMAIN D FUNCTIONAL PROOF",
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

    (directory / "DOMAIN_D_SUMMARY.txt").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    return aggregate, directory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run AEGIS RC1 Domain D functional proofs."
    )
    parser.add_argument(
        "--scenario",
        choices=sorted(SCENARIO_RUNNERS),
    )
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args(argv)
    aggregate, directory = run_domain_d(
        scenario_id=args.scenario,
        output_root=args.output_root,
    )
    print("============================================================")
    print("AEGIS DOMAIN D FUNCTIONAL PROOF")
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
