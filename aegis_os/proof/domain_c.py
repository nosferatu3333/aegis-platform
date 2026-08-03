"""Executable Domain C functional proof scenarios.

Domain C verifies the canonical authority gate and governed-runtime boundary.
It never creates or infers authority inside the system under test. Controlled
Core authority records are supplied as explicit scenario fixtures.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

SUITE_VERSION = "1.0"
RELEASE_VERSION = "1.7.0-rc1"
DOMAIN = "C"
OVERALL_PASS_VERDICT = "DOMAIN C FUNCTIONALLY VERIFIED"
SINGLE_PASS_VERDICT = "SCENARIO FUNCTIONALLY VERIFIED"
NOW = datetime(2026, 8, 2, 21, 0, tzinfo=UTC)


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _definition_path() -> Path:
    return Path(__file__).resolve().parent / "scenarios" / "domain_c.json"


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


def load_domain_c_definition() -> dict[str, Any]:
    payload = json.loads(_definition_path().read_text(encoding="utf-8-sig"))
    ids = [item["scenario_id"] for item in payload["scenarios"]]
    expected = {
        "AEGIS-RC1-S08",
        "AEGIS-RC1-S09",
        "AEGIS-RC1-S10",
        "AEGIS-RC1-S11",
    }
    if set(ids) != expected or len(ids) != len(set(ids)):
        raise ValueError("Domain C must define unique scenarios S08 through S11.")
    return payload


class _UnusedSelector:
    def select(self, task: str, **context: Any) -> Any:
        raise AssertionError("Governed proof must consume a canonical selection.")


def _selection():
    from aegis_core.contracts import (
        AuthorityRequirement,
        CapabilitySelection,
        EligibilityState,
        OperationalState,
    )

    return CapabilitySelection(
        request_id="req_c000000000000001",
        capability_id="cap_c000000000000001",
        capability_version="1.0.0",
        eligibility=EligibilityState.ELIGIBLE,
        rationale="Canonical Domain C authority proof capability.",
        health_state=OperationalState.HEALTHY,
        authority_requirement=AuthorityRequirement.APPROVAL_REQUIRED,
        selection_id="sel_c000000000000001",
    )


def _pipeline():
    from aegis_os.pipeline.request_pipeline import CognitiveRequestPipeline
    return CognitiveRequestPipeline(capability_selector=_UnusedSelector())


def _runtime():
    from aegis_os.core.governed_runtime import GovernedRuntime
    from aegis_os.execution.authority_adapter import AuthorityGatedExecutionAdapter
    from aegis_os.execution.authority_gate import AuthorityGate
    from aegis_os.execution.execution_engine import ExecutionEngine
    from aegis_os.execution.reconciliation import ExecutionResultReconciler

    return GovernedRuntime(
        pipeline=_pipeline(),
        authority_adapter=AuthorityGatedExecutionAdapter(
            gate=AuthorityGate(clock=lambda: NOW)
        ),
        execution_engine=ExecutionEngine(clock=lambda: NOW),
        reconciler=ExecutionResultReconciler(clock=lambda: NOW),
    )


def _request(*, grants=(), denials=(), execute=True):
    from aegis_os.core.governed_runtime import GovernedRuntimeRequest

    return GovernedRuntimeRequest(
        task="Perform one bounded governed change",
        interpretation_id="int_c000000000000001",
        selection=_selection(),
        selected_agent="Domain C Execution Agent",
        workflow_definition=[
            "Prepare bounded governed change",
            "Validate bounded governed change",
        ],
        execute=execute,
        grants=tuple(grants),
        denials=tuple(denials),
    )


def _analysis_only():
    return _runtime().process(_request(execute=False)).analysis


def _cached_runtime(analysis):
    runtime = _runtime()
    runtime.pipeline.process_selection = lambda **kwargs: analysis
    return runtime


def _required_scope(plan) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            scope
            for step in plan.steps
            for scope in (
                f"execute:plan:{plan.plan_id}",
                f"execute:step:{step.step_id}",
            )
        )
    )


def _full_grant(plan):
    from aegis_core.contracts import (
        AuthorityGrant,
        AuthoritySource,
        ConsequenceClass,
    )

    return AuthorityGrant(
        grant_id="grt_c000000000000001",
        subject_type="bounded_plan",
        subject_id=plan.plan_id,
        grantee_id="svc_aegis_platform",
        granted_scope=_required_scope(plan),
        consequence_ceiling=ConsequenceClass.HIGH,
        issued_by="usr_c000000000000001",
        source=AuthoritySource.SYSTEM_POLICY,
        issued_at=NOW - timedelta(minutes=2),
        valid_from=NOW - timedelta(minutes=1),
    )


def _base(definition: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "suite_version": SUITE_VERSION,
        "release_version": RELEASE_VERSION,
        "domain": DOMAIN,
        "scenario_id": definition["scenario_id"],
        "title": definition["title"],
        "expected_canonical_outcome": definition["expected_canonical_outcome"],
        "actual_canonical_outcome": None,
        "started_at": _utc_now(),
        "completed_at": None,
        "passed": False,
        "assertions": [],
        "evidence": {},
        "failure_reason": None,
        "declared_boundary": {
            "execution_mode": "deterministic governed simulation",
            "authority_is_inferred": False,
            "real_world_execution_claimed": False,
            "production_readiness_claimed": False,
        },
    }


def _check(result: dict[str, Any], name: str, condition: bool, detail: str) -> None:
    result["assertions"].append(
        {"name": name, "passed": bool(condition), "detail": detail}
    )


def _finish(result: dict[str, Any]) -> dict[str, Any]:
    result["passed"] = bool(result["assertions"]) and all(
        item["passed"] for item in result["assertions"]
    )
    if not result["passed"]:
        failed = [item["name"] for item in result["assertions"] if not item["passed"]]
        result["failure_reason"] = "Failed assertions: " + ", ".join(failed)
    result["completed_at"] = _utc_now()
    return result


def _authority_payload(authority) -> dict[str, Any]:
    return {
        "ready": authority.ready,
        "paused": authority.paused,
        "denied": authority.denied,
        "decisions": [
            {
                "step_id": item.step_id,
                "sequence": item.sequence,
                "outcome": item.outcome.value,
                "reason": item.reason,
                "requested_scope": list(item.requested_scope),
                "grant_id": item.grant_id,
                "audit_event_id": item.audit_event.event_id,
            }
            for item in authority.decisions
        ],
    }


def _s08(definition: dict[str, Any]) -> dict[str, Any]:
    from aegis_os.core.governed_runtime import GovernedRuntimeStatus

    result = _base(definition)
    analysis = _analysis_only()
    plan = analysis.canonical_plan
    grant = _full_grant(plan)
    governed = _cached_runtime(analysis).process(_request(grants=(grant,)))

    result["actual_canonical_outcome"] = governed.status.value
    result["evidence"] = {
        "plan": plan.to_dict(),
        "grant_id": grant.grant_id,
        "granted_scope": list(grant.granted_scope),
        "authority": _authority_payload(governed.authority),
        "execution": governed.execution.to_dict() if governed.execution else None,
        "validation": governed.validation.to_dict() if governed.validation else None,
        "reconciliation": {
            "outcome": governed.reconciliation.outcome.value,
            "result_id": governed.reconciliation.result.result_id,
            "trace_complete": governed.reconciliation.trace.is_complete_result_trace,
        } if governed.reconciliation else None,
    }

    _check(result, "completed", governed.status is GovernedRuntimeStatus.COMPLETED, governed.status.value)
    _check(result, "all_steps_allowed", governed.authority.ready and all(d.outcome.value == "allow" for d in governed.authority.decisions), str([d.outcome.value for d in governed.authority.decisions]))
    _check(result, "execution_performed", governed.execution_performed is True and governed.execution is not None, str(governed.execution_performed))
    _check(result, "conformance_passed", governed.validation is not None and governed.validation.status.value == "passed", governed.validation.status.value if governed.validation else "missing")
    _check(result, "reconciled", governed.reconciliation is not None and governed.reconciliation.trace.is_complete_result_trace, "complete result trace required")
    return _finish(result)


def _s09(definition: dict[str, Any]) -> dict[str, Any]:
    from aegis_os.core.governed_runtime import GovernedRuntimeStatus

    result = _base(definition)
    analysis = _analysis_only()
    governed = _cached_runtime(analysis).process(_request())

    result["actual_canonical_outcome"] = governed.status.value
    result["evidence"] = {
        "plan": analysis.canonical_plan.to_dict(),
        "authority": _authority_payload(governed.authority),
        "execution": None,
    }

    _check(result, "paused", governed.status is GovernedRuntimeStatus.PAUSED, governed.status.value)
    _check(result, "missing_grant_reported", all("No effective authority grant" in d.reason for d in governed.authority.decisions), str([d.reason for d in governed.authority.decisions]))
    _check(result, "no_execution_request", governed.authority.execution_request is None, "authority adapter must not emit request")
    _check(result, "execution_not_performed", governed.execution_performed is False and governed.execution is None, str(governed.execution_performed))
    return _finish(result)


def _s10(definition: dict[str, Any]) -> dict[str, Any]:
    from aegis_core.contracts import AuthorityDenial
    from aegis_os.core.governed_runtime import GovernedRuntimeStatus

    result = _base(definition)
    analysis = _analysis_only()
    plan = analysis.canonical_plan
    grant = _full_grant(plan)
    denial = AuthorityDenial(
        denial_id="dny_c000000000000001",
        subject_type="bounded_plan_step",
        subject_id=plan.steps[0].step_id,
        denied_scope=(f"execute:step:{plan.steps[0].step_id}",),
        denied_by="usr_c000000000000001",
        reason="Controlled Domain C denial.",
        denied_at=NOW,
    )
    governed = _cached_runtime(analysis).process(
        _request(grants=(grant,), denials=(denial,))
    )

    outcomes = [item.outcome.value for item in governed.authority.decisions]
    result["actual_canonical_outcome"] = governed.status.value
    result["evidence"] = {
        "plan": plan.to_dict(),
        "grant_id": grant.grant_id,
        "denial_id": denial.denial_id,
        "authority": _authority_payload(governed.authority),
        "execution": None,
    }

    _check(result, "denied", governed.status is GovernedRuntimeStatus.DENIED, governed.status.value)
    _check(result, "denial_precedence", "deny" in outcomes, str(outcomes))
    _check(result, "denial_reason_preserved", any(denial.denial_id in item.reason for item in governed.authority.decisions), str([d.reason for d in governed.authority.decisions]))
    _check(result, "execution_blocked", governed.execution_performed is False and governed.execution is None, str(governed.execution_performed))
    return _finish(result)


def _s11(definition: dict[str, Any]) -> dict[str, Any]:
    from aegis_core.contracts import (
        AuthorityGrant,
        AuthoritySource,
        ConsequenceClass,
    )
    from aegis_os.core.governed_runtime import GovernedRuntimeStatus

    result = _base(definition)
    analysis = _analysis_only()
    plan = analysis.canonical_plan
    partial = AuthorityGrant(
        grant_id="grt_c000000000000002",
        subject_type="bounded_plan",
        subject_id=plan.plan_id,
        grantee_id="svc_aegis_platform",
        granted_scope=(f"execute:plan:{plan.plan_id}",),
        consequence_ceiling=ConsequenceClass.HIGH,
        issued_by="usr_c000000000000001",
        source=AuthoritySource.SYSTEM_POLICY,
        issued_at=NOW - timedelta(minutes=2),
        valid_from=NOW - timedelta(minutes=1),
    )
    governed = _cached_runtime(analysis).process(_request(grants=(partial,)))

    result["actual_canonical_outcome"] = governed.status.value
    result["evidence"] = {
        "plan": plan.to_dict(),
        "grant_id": partial.grant_id,
        "granted_scope": list(partial.granted_scope),
        "required_scope": list(_required_scope(plan)),
        "authority": _authority_payload(governed.authority),
        "execution": None,
    }

    _check(result, "paused", governed.status is GovernedRuntimeStatus.PAUSED, governed.status.value)
    _check(result, "scope_incomplete", set(partial.granted_scope) < set(_required_scope(plan)), "partial grant omits every step scope")
    _check(result, "no_step_allowed_by_partial_scope", all(item.outcome.value == "pause" for item in governed.authority.decisions), str([d.outcome.value for d in governed.authority.decisions]))
    _check(result, "execution_blocked", governed.execution_performed is False and governed.execution is None, str(governed.execution_performed))
    return _finish(result)


RUNNERS = {
    "AEGIS-RC1-S08": _s08,
    "AEGIS-RC1-S09": _s09,
    "AEGIS-RC1-S10": _s10,
    "AEGIS-RC1-S11": _s11,
}


def run_domain_c(
    *,
    scenario_id: str | None = None,
    output_root: Path | None = None,
) -> tuple[dict[str, Any], Path]:
    payload = load_domain_c_definition()
    definitions = payload["scenarios"]
    if scenario_id is not None:
        definitions = [item for item in definitions if item["scenario_id"] == scenario_id]
        if not definitions:
            raise ValueError(f"Unknown Domain C scenario: {scenario_id}")

    root = output_root or (_root() / "artifacts" / "functional-proof" / "domain-c")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(root) / stamp
    suffix = 1
    while run_dir.exists():
        run_dir = Path(root) / f"{stamp}-{suffix}"
        suffix += 1
    run_dir.mkdir(parents=True)

    results = []
    for definition in definitions:
        try:
            result = RUNNERS[definition["scenario_id"]](definition)
        except Exception as error:
            result = _base(definition)
            result["actual_canonical_outcome"] = "blocked"
            result["failure_reason"] = f"{type(error).__name__}: {error}"
            result["completed_at"] = _utc_now()
        (run_dir / f"{definition['scenario_id']}.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        results.append(result)

    passed = sum(item["passed"] for item in results)
    blocked = sum(item["actual_canonical_outcome"] == "blocked" for item in results)
    failed = len(results) - passed - blocked
    all_passed = passed == len(results) and failed == 0 and blocked == 0

    aggregate = {
        "schema_version": "1.0",
        "suite_version": SUITE_VERSION,
        "release_version": RELEASE_VERSION,
        "domain": DOMAIN,
        "domain_title": payload["domain_title"],
        "scenarios_executed": len(results),
        "passed": passed,
        "failed": failed,
        "blocked": blocked,
        "scenario_summaries": [
            {
                "scenario_id": item["scenario_id"],
                "actual_canonical_outcome": item["actual_canonical_outcome"],
                "passed": item["passed"],
                "failure_reason": item["failure_reason"],
            }
            for item in results
        ],
        "overall_domain_verdict": (
            (OVERALL_PASS_VERDICT if scenario_id is None else SINGLE_PASS_VERDICT)
            if all_passed
            else "DOMAIN C VERIFICATION FAILED"
        ),
        "repository_commit": _git_value("rev-parse", "HEAD"),
        "repository_tree": _git_value("rev-parse", "HEAD^{tree}"),
        "generated_output_is_signed_release": False,
        "private_signing_material_included": False,
        "declared_boundary": payload["declared_boundary"],
    }
    (run_dir / "DOMAIN_C_REPORT.json").write_text(
        json.dumps(aggregate, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    lines = [
        "============================================================",
        "AEGIS DOMAIN C FUNCTIONAL PROOF",
        "============================================================",
        f"Scenarios executed: {aggregate['scenarios_executed']}",
        f"Passed: {passed}",
        f"Failed: {failed}",
        f"Blocked: {blocked}",
        f"Verdict: {aggregate['overall_domain_verdict']}",
        f"Evidence: {run_dir}",
        "",
    ]
    for item in results:
        marker = "PASS" if item["passed"] else "FAIL"
        lines.append(
            f"[{marker}] {item['scenario_id']} - {item['actual_canonical_outcome']}"
        )
    (run_dir / "DOMAIN_C_SUMMARY.txt").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    return aggregate, run_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run AEGIS RC1 Domain C proofs.")
    parser.add_argument("--scenario", choices=sorted(RUNNERS))
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args(argv)
    aggregate, run_dir = run_domain_c(
        scenario_id=args.scenario,
        output_root=args.output_root,
    )
    print("============================================================")
    print("AEGIS DOMAIN C FUNCTIONAL PROOF")
    print("============================================================")
    print(f"Scenarios executed: {aggregate['scenarios_executed']}")
    print(f"Passed: {aggregate['passed']}")
    print(f"Failed: {aggregate['failed']}")
    print(f"Blocked: {aggregate['blocked']}")
    print(f"Verdict: {aggregate['overall_domain_verdict']}")
    print(f"Evidence: {run_dir}")
    return 0 if aggregate["failed"] == 0 and aggregate["blocked"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
