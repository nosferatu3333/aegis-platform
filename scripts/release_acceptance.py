"""Run deterministic governed-runtime acceptance scenarios for the MVP release."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aegis_core.contracts import (
    AuthorityDenial,
    AuthorityRequirement,
    CapabilitySelection,
    EligibilityState,
    OperationalState,
)
from aegis_os.core.governed_runtime import (
    GovernedRuntimeRequest,
    GovernedRuntimeStatus,
)
from aegis_os.pipeline.composition import create_governed_runtime
from aegis_os.release import PLATFORM_VERSION

RELEASE = PLATFORM_VERSION
REQUEST_ID = "req_1234567890abcdef"
INTERPRETATION_ID = "int_1234567890abcdef"
SELECTION_ID = "sel_1234567890abcdef"
ACTOR_ID = "usr_1234567890abcdef"


def _selection(authority: AuthorityRequirement) -> CapabilitySelection:
    return CapabilitySelection(
        request_id=REQUEST_ID,
        capability_id="cap_iterative_ai_development",
        capability_version="0.2.0",
        eligibility=EligibilityState.ELIGIBLE,
        rationale="Canonical capability selected for release acceptance.",
        health_state=OperationalState.HEALTHY,
        authority_requirement=authority,
        selection_id=SELECTION_ID,
    )


def _request(
    *,
    authority: AuthorityRequirement = AuthorityRequirement.NONE,
    execute: bool = True,
    workflow: list[str] | None = None,
    denials: tuple[AuthorityDenial, ...] = (),
) -> GovernedRuntimeRequest:
    return GovernedRuntimeRequest(
        task="Perform deterministic MVP release acceptance work",
        interpretation_id=INTERPRETATION_ID,
        selection=_selection(authority),
        selected_agent="Execution Agent",
        workflow_definition=workflow or ["Prepare bounded work", "Verify evidence"],
        execute=execute,
        denials=denials,
    )


def run_acceptance() -> dict[str, Any]:
    runtime = create_governed_runtime()

    analyzed = runtime.process(_request(execute=False))
    completed = runtime.process(_request())
    paused = runtime.process(
        _request(authority=AuthorityRequirement.APPROVAL_REQUIRED)
    )

    denied_analysis = runtime.process(_request(execute=False))
    denied_plan = denied_analysis.analysis.canonical_plan
    if denied_plan is None:
        raise RuntimeError("acceptance analysis did not produce a bounded plan")
    denial = AuthorityDenial(
        subject_type="bounded_plan",
        subject_id=denied_plan.plan_id,
        denied_scope=(f"execute:step:{denied_plan.steps[0].step_id}",),
        denied_by=ACTOR_ID,
        reason="Release acceptance explicit denial.",
        denied_at=datetime.now(UTC),
    )
    denied_runtime = create_governed_runtime()
    denied_runtime.pipeline.process_selection = lambda **_: denied_analysis.analysis
    denied = denied_runtime.process(_request(denials=(denial,)))

    failed = runtime.process(
        _request(workflow=["Prepare bounded work", "[simulate-failure]", "Never run"])
    )

    scenarios = {
        "analyzed": analyzed,
        "completed": completed,
        "paused": paused,
        "denied": denied,
        "failed": failed,
    }
    expected = {
        "analyzed": GovernedRuntimeStatus.ANALYZED,
        "completed": GovernedRuntimeStatus.COMPLETED,
        "paused": GovernedRuntimeStatus.PAUSED,
        "denied": GovernedRuntimeStatus.DENIED,
        "failed": GovernedRuntimeStatus.FAILED,
    }

    entries: list[dict[str, Any]] = []
    passed = True
    for name, result in scenarios.items():
        scenario_passed = result.status is expected[name]
        passed = passed and scenario_passed
        entries.append(
            {
                "scenario": name,
                "expected_status": expected[name].value,
                "actual_status": result.status.value,
                "passed": scenario_passed,
                "execution_requested": result.execution_requested,
                "execution_performed": result.execution_performed,
                "authority_ready": result.authority.ready if result.authority else None,
                "reconciliation_outcome": (
                    result.reconciliation.outcome.value
                    if result.reconciliation is not None
                    else None
                ),
                "simulated": True,
            }
        )

    return {
        "release": f"AEGIS Platform MVP {RELEASE}",
        "platform_version": RELEASE,
        "accepted": passed,
        "execution_mode": "deterministic simulation only",
        "real_world_effects_verified": False,
        "scenario_count": len(entries),
        "scenarios": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = run_acceptance()
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(payload, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
