"""Executable Domain B functional proof scenarios.

Domain B proves canonical bounded planning and execution-boundary contracts.

S06 uses the production PlanningBounds contract. RC1 does not yet contain a
semantic scope classifier, so the scenario proves that workflow expansion
beyond an explicit bound is rejected before an expanded plan is emitted.

S07 uses a controlled stop-condition fixture with the production execution,
cancellation, and conformance contracts. RC1 recognizes canonical cancelled
receipts but does not yet expose a live runtime stop-request hook.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

SUITE_VERSION = "1.0"
RELEASE_VERSION = "1.7.0-rc1"
DOMAIN = "B"

OVERALL_PASS_VERDICT = "DOMAIN B FUNCTIONALLY VERIFIED"
SINGLE_PASS_VERDICT = "SCENARIO FUNCTIONALLY VERIFIED"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _scenario_path() -> Path:
    return Path(__file__).resolve().parent / "scenarios" / "domain_b.json"


def _git_value(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=_repository_root(),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def load_domain_b_definition() -> dict[str, Any]:
    payload = json.loads(_scenario_path().read_text(encoding="utf-8-sig"))
    identifiers = [
        scenario.get("scenario_id")
        for scenario in payload.get("scenarios", [])
    ]
    expected = {"AEGIS-RC1-S05", "AEGIS-RC1-S06", "AEGIS-RC1-S07"}
    if set(identifiers) != expected:
        raise ValueError("Domain B must define exactly S05 through S07.")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Domain B scenario identifiers must be unique.")
    return payload


def _selection(suffix: str) -> Any:
    from aegis_core.contracts import (
        AuthorityRequirement,
        CapabilitySelection,
        EligibilityState,
        OperationalState,
    )

    return CapabilitySelection(
        request_id=f"req_domainb{suffix}",
        capability_id="cap_domain_b_planning",
        capability_version="1.0.0",
        eligibility=EligibilityState.ELIGIBLE,
        rationale="Canonical Domain B planning capability.",
        health_state=OperationalState.HEALTHY,
        authority_requirement=AuthorityRequirement.NONE,
        selection_id=f"sel_domainb{suffix}",
    )


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
        "plan_id": None,
        "selection_id": None,
        "execution_requested": bool(definition["execution_requested"]),
        "execution_performed": False,
        "assertions": [],
        "evidence": {},
        "failure_reason": None,
        "declared_boundary": {
            "execution_mode": "deterministic governed simulation",
            "semantic_scope_classifier_present": False,
            "live_stop_request_hook_present": False,
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
        {"name": name, "passed": bool(condition), "detail": detail}
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


def _scenario_s05(definition: dict[str, Any]) -> dict[str, Any]:
    from aegis_os.pipeline.bounded_planning_adapter import (
        BoundedPlanningAdapter,
        PlanningBounds,
    )
    from aegis_os.pipeline.request_pipeline import CognitiveRequestPipeline

    class UnusedSelector:
        def select(self, task: str, **context: Any) -> Any:
            raise AssertionError(
                "process_selection must not invoke the legacy selector"
            )

    result = _base_result(definition)
    selection = _selection("0500000001")
    pipeline = CognitiveRequestPipeline(
        capability_selector=UnusedSelector(),
        bounded_planning_adapter=BoundedPlanningAdapter(
            bounds=PlanningBounds(max_steps=4)
        ),
    )
    analysis = pipeline.process_selection(
        task=definition["mission"],
        interpretation_id="int_domainb0500000001",
        selection=selection,
        workflow_definition=[
            {
                "title": "Inspect response contract",
                "description": "Document the existing API response field boundary.",
            },
            {
                "title": "Define one field change",
                "description": "Specify exactly one validated response-field change.",
            },
            {
                "title": "Define validation evidence",
                "description": "Record the checks required to accept the change.",
            },
        ],
    )
    plan = analysis.canonical_plan
    if plan is None:
        raise RuntimeError("Canonical pipeline did not produce a bounded plan.")

    sequences = [step.sequence for step in plan.steps]
    criteria = [list(step.completion_criteria) for step in plan.steps]
    result["actual_canonical_outcome"] = analysis.status.value
    result["request_id"] = plan.request_id
    result["plan_id"] = plan.plan_id
    result["selection_id"] = plan.selection_id
    result["evidence"] = {
        "analysis": analysis.to_dict(),
        "canonical_plan": plan.to_dict(),
        "configured_max_steps": 4,
        "actual_step_count": len(plan.steps),
        "step_sequences": sequences,
        "completion_criteria": criteria,
    }

    _assert(result, "canonical_plan_present", plan is not None, f"Plan ID: {plan.plan_id}")
    _assert(
        result,
        "objective_preserved",
        plan.objective == definition["mission"],
        f"Objective: {plan.objective}",
    )
    _assert(
        result,
        "plan_is_finite",
        0 < len(plan.steps) <= 4,
        f"Step count: {len(plan.steps)}; maximum: 4",
    )
    _assert(
        result,
        "step_sequence_is_contiguous",
        sequences == list(range(1, len(plan.steps) + 1)),
        f"Sequences: {sequences}",
    )
    _assert(
        result,
        "completion_criteria_present",
        all(item for item in criteria),
        f"Criteria groups: {len(criteria)}",
    )
    _assert(
        result,
        "expected_evidence_present",
        bool(plan.expected_evidence),
        f"Evidence requirements: {len(plan.expected_evidence)}",
    )
    _assert(
        result,
        "planning_boundary_declared",
        any(
            "no step has been executed" in item.lower()
            for item in plan.limitations
        ),
        f"Limitations: {list(plan.limitations)}",
    )
    _assert(
        result,
        "execution_not_performed",
        result["execution_performed"] is False,
        "process_selection creates a plan but invokes no executor.",
    )
    return _finish(result)


def _scenario_s06(definition: dict[str, Any]) -> dict[str, Any]:
    from aegis_os.pipeline.bounded_planning_adapter import (
        BoundedPlanningAdapter,
        BoundedPlanningAdapterError,
        PlanningBounds,
    )
    from aegis_os.pipeline.models import WorkflowStep

    result = _base_result(definition)
    selection = _selection("0600000001")
    adapter = BoundedPlanningAdapter(bounds=PlanningBounds(max_steps=3))
    accepted_workflow = [
        WorkflowStep(
            order=1,
            title="Inspect response field",
            description="Inspect the existing API response field.",
            capability_id=selection.capability_id,
        ),
        WorkflowStep(
            order=2,
            title="Prepare bounded field update",
            description="Prepare only the requested response-field update.",
            capability_id=selection.capability_id,
        ),
        WorkflowStep(
            order=3,
            title="Validate response field",
            description="Validate only the requested response-field update.",
            capability_id=selection.capability_id,
        ),
    ]
    accepted_plan = adapter.build(
        selection=selection,
        interpretation_id="int_domainb0600000001",
        objective=definition["mission"],
        workflow=accepted_workflow,
        limitations=(
            "Only one API response field may be changed.",
            "Authentication configuration is outside the declared scope.",
        ),
        stop_conditions=(
            "Stop when the workflow expands beyond three steps.",
            "Stop when unrelated configuration is introduced.",
        ),
    )
    injected_step = WorkflowStep(
        order=4,
        title="Modify authentication configuration",
        description="Modify unrelated authentication configuration.",
        capability_id=selection.capability_id,
    )
    expanded_plan = None
    planning_error = None
    try:
        expanded_plan = adapter.build(
            selection=selection,
            interpretation_id="int_domainb0600000002",
            objective=definition["mission"],
            workflow=[*accepted_workflow, injected_step],
            limitations=accepted_plan.limitations,
            stop_conditions=accepted_plan.stop_conditions,
        )
    except BoundedPlanningAdapterError as error:
        planning_error = error

    result["actual_canonical_outcome"] = (
        "planning_bounds_rejected_expansion"
        if planning_error is not None
        else "expanded_plan_accepted"
    )
    result["request_id"] = accepted_plan.request_id
    result["plan_id"] = accepted_plan.plan_id
    result["selection_id"] = accepted_plan.selection_id
    result["evidence"] = {
        "scope_detection_mode": "explicit_max_steps_boundary",
        "semantic_scope_classifier_present": False,
        "configured_max_steps": 3,
        "accepted_plan": accepted_plan.to_dict(),
        "accepted_step_count": len(accepted_plan.steps),
        "injected_step": injected_step.to_dict(),
        "expanded_workflow_step_count": 4,
        "expanded_plan_emitted": expanded_plan is not None,
        "planning_error_type": (
            type(planning_error).__name__ if planning_error is not None else None
        ),
        "planning_error": (
            str(planning_error) if planning_error is not None else None
        ),
    }

    _assert(
        result,
        "baseline_plan_accepted",
        len(accepted_plan.steps) == 3,
        f"Accepted baseline steps: {len(accepted_plan.steps)}",
    )
    _assert(
        result,
        "expansion_rejected",
        planning_error is not None,
        f"Planning error: {planning_error}",
    )
    _assert(
        result,
        "production_bounds_error_used",
        isinstance(planning_error, BoundedPlanningAdapterError),
        f"Error type: {type(planning_error).__name__ if planning_error else None}",
    )
    _assert(
        result,
        "configured_maximum_reported",
        planning_error is not None and "maximum of 3" in str(planning_error),
        f"Error: {planning_error}",
    )
    _assert(
        result,
        "expanded_plan_not_emitted",
        expanded_plan is None,
        f"Expanded plan emitted: {expanded_plan is not None}",
    )
    _assert(
        result,
        "injected_action_is_outside_declared_limitations",
        any("authentication" in item.lower() for item in accepted_plan.limitations),
        f"Limitations: {list(accepted_plan.limitations)}",
    )
    _assert(
        result,
        "execution_not_performed",
        result["execution_performed"] is False,
        "The rejected workflow never reaches execution.",
    )
    return _finish(result)


def _scenario_s07(definition: dict[str, Any]) -> dict[str, Any]:
    from aegis_os.execution.adapter import build_execution_request
    from aegis_os.execution.conformance import (
        ConformanceStatus,
        ExecutionConformanceValidator,
    )
    from aegis_os.execution.execution_engine import ExecutionEngine
    from aegis_os.execution.models import ExecutionStatus, ExecutionStepStatus
    from aegis_os.pipeline.bounded_planning_adapter import (
        BoundedPlanningAdapter,
        PlanningBounds,
    )
    from aegis_os.pipeline.intent_analyzer import IntentAnalyzer
    from aegis_os.pipeline.models import (
        CapabilityMatch,
        CognitiveRequestResult,
        PipelineStatus,
        WorkflowStep,
    )

    result = _base_result(definition)
    selection = _selection("0700000001")
    workflow = [
        WorkflowStep(
            order=1,
            title="Verify baseline",
            description="Verify the authorized repository baseline.",
            capability_id=selection.capability_id,
        ),
        WorkflowStep(
            order=2,
            title="Prepare bounded change",
            description="Prepare the approved bounded change.",
            capability_id=selection.capability_id,
        ),
        WorkflowStep(
            order=3,
            title="Validate bounded change",
            description="Validate the approved bounded change.",
            capability_id=selection.capability_id,
        ),
    ]
    stop_condition = "Stop if the repository baseline changes."
    plan = BoundedPlanningAdapter(
        bounds=PlanningBounds(max_steps=3)
    ).build(
        selection=selection,
        interpretation_id="int_domainb0700000001",
        objective=definition["mission"],
        workflow=workflow,
        expected_evidence=(
            "Authorized baseline identity",
            "Completed-step evidence",
            "Cancellation evidence for skipped work",
        ),
        assumptions=("The baseline is verified before the first step.",),
        limitations=("No work may continue after a baseline mismatch.",),
        stop_conditions=(stop_condition,),
    )
    analysis = CognitiveRequestResult(
        task=definition["mission"],
        intent=IntentAnalyzer().analyze(definition["mission"]),
        capability=CapabilityMatch(
            capability_id=selection.capability_id,
            name=selection.capability_id,
            confidence=1.0,
            score=1.0,
            reasons=("Canonical Domain B cancellation proof.",),
        ),
        workflow=workflow,
        status=PipelineStatus.READY,
        metadata={
            "planning_boundary": "bounded_non_executing",
            "stop_condition_fixture": True,
        },
        canonical_plan=plan,
    )
    execution_request = build_execution_request(
        analysis,
        selection.request_id,
        constraints=list(plan.stop_conditions),
        permissions=["simulated_workflow_execution"],
        metadata={
            "canonical_plan_id": plan.plan_id,
            "controlled_stop_fixture": True,
        },
    )
    fixed_time = datetime(2026, 8, 2, 20, 0, tzinfo=UTC)
    receipt = ExecutionEngine(clock=lambda: fixed_time).execute(execution_request)

    completed_prefix = 1
    receipt.status = ExecutionStatus.CANCELLED
    receipt.completed_steps = completed_prefix
    receipt.failed_steps = 0
    receipt.finished_at = fixed_time
    for index, step in enumerate(receipt.steps):
        if index < completed_prefix:
            step.status = ExecutionStepStatus.COMPLETED
        else:
            step.status = ExecutionStepStatus.SKIPPED
            step.outputs = {}
            step.error = None
    receipt.logs.append(
        "controlled stop condition activated: "
        "repository baseline changed; simulated=true"
    )
    validation = ExecutionConformanceValidator().validate(
        request_id=selection.request_id,
        analysis=analysis,
        execution_request=execution_request,
        receipt=receipt,
    )
    statuses = [step.status.value for step in receipt.steps]
    skipped_outputs = [
        step.outputs for step in receipt.steps[completed_prefix:]
    ]

    result["actual_canonical_outcome"] = receipt.status.value
    result["request_id"] = plan.request_id
    result["plan_id"] = plan.plan_id
    result["selection_id"] = plan.selection_id
    result["execution_performed"] = True
    result["evidence"] = {
        "activation_mode": "controlled canonical cancellation fixture",
        "live_stop_request_hook_present": False,
        "trigger": "repository baseline changed",
        "triggered_stop_condition": stop_condition,
        "canonical_plan": plan.to_dict(),
        "execution_request": execution_request.to_dict(),
        "execution_receipt": receipt.to_dict(),
        "conformance": validation.to_dict(),
        "completed_prefix": completed_prefix,
        "step_statuses": statuses,
        "skipped_step_outputs": skipped_outputs,
    }

    _assert(
        result,
        "stop_condition_recorded",
        stop_condition in plan.stop_conditions,
        f"Stop conditions: {list(plan.stop_conditions)}",
    )
    _assert(
        result,
        "receipt_is_cancelled",
        receipt.status is ExecutionStatus.CANCELLED,
        f"Receipt status: {receipt.status.value}",
    )
    _assert(
        result,
        "completed_prefix_preserved",
        statuses[:completed_prefix] == [ExecutionStepStatus.COMPLETED.value],
        f"Completed prefix: {statuses[:completed_prefix]}",
    )
    _assert(
        result,
        "remaining_steps_skipped",
        all(
            status == ExecutionStepStatus.SKIPPED.value
            for status in statuses[completed_prefix:]
        ),
        f"Remaining statuses: {statuses[completed_prefix:]}",
    )
    _assert(
        result,
        "skipped_steps_have_no_completion_outputs",
        all(not output for output in skipped_outputs),
        f"Skipped outputs: {skipped_outputs}",
    )
    _assert(
        result,
        "no_failure_step_fabricated",
        receipt.failed_steps == 0
        and all(
            step.status is not ExecutionStepStatus.FAILED
            for step in receipt.steps
        ),
        f"Failed steps: {receipt.failed_steps}",
    )
    _assert(
        result,
        "cancellation_conformance_passed",
        validation.status is ConformanceStatus.PASSED,
        f"Conformance status: {validation.status.value}",
    )
    _assert(
        result,
        "no_false_completed_outcome",
        receipt.status is not ExecutionStatus.COMPLETED,
        f"Terminal outcome: {receipt.status.value}",
    )
    return _finish(result)


SCENARIO_RUNNERS = {
    "AEGIS-RC1-S05": _scenario_s05,
    "AEGIS-RC1-S06": _scenario_s06,
    "AEGIS-RC1-S07": _scenario_s07,
}


def _selected_definitions(
    payload: dict[str, Any],
    scenario_id: str | None,
) -> Iterable[dict[str, Any]]:
    if scenario_id is None:
        return payload["scenarios"]
    selected = [
        scenario
        for scenario in payload["scenarios"]
        if scenario["scenario_id"] == scenario_id
    ]
    if not selected:
        raise ValueError(f"Unknown Domain B scenario: {scenario_id}")
    return selected


def run_domain_b(
    *,
    scenario_id: str | None = None,
    output_root: Path | None = None,
) -> tuple[dict[str, Any], Path]:
    payload = load_domain_b_definition()
    started_at = _utc_now()
    run_stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    root = (
        Path(output_root)
        if output_root is not None
        else _repository_root()
        / "artifacts"
        / "functional-proof"
        / "domain-b"
    )
    run_directory = root / run_stamp
    suffix = 1
    while run_directory.exists():
        run_directory = root / f"{run_stamp}-{suffix}"
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
            scenario_result["failure_reason"] = f"{type(error).__name__}: {error}"
            scenario_result["completed_at"] = _utc_now()
        (run_directory / f"{definition['scenario_id']}.json").write_text(
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
                "actual_canonical_outcome": result["actual_canonical_outcome"],
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
            else "DOMAIN B VERIFICATION FAILED"
        ),
        "repository_commit": _git_value("rev-parse", "HEAD"),
        "repository_tree": _git_value("rev-parse", "HEAD^{tree}"),
        "generated_output_is_signed_release": False,
        "private_signing_material_included": False,
        "declared_boundary": payload["declared_boundary"],
    }
    (run_directory / "DOMAIN_B_REPORT.json").write_text(
        json.dumps(aggregate, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    summary_lines = [
        "============================================================",
        "AEGIS DOMAIN B FUNCTIONAL PROOF",
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
            f"[{marker}] {result['scenario_id']} - "
            f"{result['actual_canonical_outcome']}"
        )
    (run_directory / "DOMAIN_B_SUMMARY.txt").write_text(
        "\n".join(summary_lines) + "\n",
        encoding="utf-8",
    )
    return aggregate, run_directory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run AEGIS RC1 Domain B functional proof scenarios."
    )
    parser.add_argument(
        "--scenario",
        choices=sorted(SCENARIO_RUNNERS),
        help="Run one canonical Domain B scenario.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        help="Optional evidence-output root.",
    )
    args = parser.parse_args(argv)
    aggregate, run_directory = run_domain_b(
        scenario_id=args.scenario,
        output_root=args.output_root,
    )
    print("============================================================")
    print("AEGIS DOMAIN B FUNCTIONAL PROOF")
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
            and aggregate["passed"] == aggregate["scenarios_executed"]
        )
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
