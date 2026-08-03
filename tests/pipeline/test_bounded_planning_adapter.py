import pytest

from aegis_core.contracts import (
    AuthorityRequirement,
    CapabilitySelection,
    ConsequenceClass,
    EligibilityState,
    OperationalState,
)
from aegis_os.pipeline.bounded_planning_adapter import (
    BoundedPlanningAdapter,
    BoundedPlanningAdapterError,
    PlanningBounds,
)
from aegis_os.pipeline.models import IntentAnalysis, RiskLevel, WorkflowStep
from aegis_os.pipeline.request_pipeline import CognitiveRequestPipeline


def selection(*, authority=AuthorityRequirement.NONE):
    return CapabilitySelection(
        request_id="req_1234567890abcdef",
        capability_id="cap_iterative_ai_development",
        capability_version="0.2.0",
        eligibility=EligibilityState.ELIGIBLE,
        rationale="Best eligible capability for the requested work.",
        health_state=OperationalState.HEALTHY,
        authority_requirement=authority,
        selection_id="sel_1234567890abcdef",
    )


def test_adapter_builds_canonical_non_executing_plan():
    adapter = BoundedPlanningAdapter()
    plan = adapter.build(
        selection=selection(),
        interpretation_id="int_1234567890abcdef",
        objective="Build the smallest useful release",
        workflow=[
            WorkflowStep(
                order=1,
                title="Define scope",
                description="Record the bounded release scope.",
            ),
            WorkflowStep(
                order=2,
                title="Validate result",
                description="Verify acceptance evidence.",
            ),
        ],
    )

    assert plan.request_id == "req_1234567890abcdef"
    assert plan.selection_id == "sel_1234567890abcdef"
    assert [step.sequence for step in plan.steps] == [1, 2]
    assert plan.steps[0].authority_requirement is AuthorityRequirement.NONE
    assert plan.expected_evidence
    assert "no step has been executed" in plan.limitations[-1].lower()


def test_consequential_plan_gets_stop_conditions_and_preserves_authority():
    adapter = BoundedPlanningAdapter()
    plan = adapter.build(
        selection=selection(authority=AuthorityRequirement.APPROVAL_REQUIRED),
        interpretation_id="int_1234567890abcdef",
        objective="Prepare a controlled production change",
        workflow=["Prepare change", "Verify change"],
        intent=IntentAnalysis(
            primary_intent="execution",
            risk=RiskLevel.HIGH,
            requires_planning=True,
            requires_execution=True,
        ),
    )

    assert plan.consequence_class is ConsequenceClass.HIGH
    assert plan.stop_conditions
    assert any("approval" in condition.lower() for condition in plan.stop_conditions)
    assert all(
        step.authority_requirement is AuthorityRequirement.APPROVAL_REQUIRED
        for step in plan.steps
    )


def test_adapter_rejects_workflow_beyond_configured_bound():
    adapter = BoundedPlanningAdapter(bounds=PlanningBounds(max_steps=2))

    with pytest.raises(BoundedPlanningAdapterError, match="maximum of 2"):
        adapter.build(
            selection=selection(),
            interpretation_id="int_1234567890abcdef",
            objective="Bounded work",
            workflow=["one", "two", "three"],
        )


def test_pipeline_accepts_canonical_selection_and_serializes_plan():
    class UnusedSelector:
        def select(self, task, **context):
            raise AssertionError("legacy selector must not be called")

    pipeline = CognitiveRequestPipeline(capability_selector=UnusedSelector())
    result = pipeline.process_selection(
        task="Design an AI implementation plan",
        interpretation_id="int_1234567890abcdef",
        selection=selection(),
        workflow_definition=[
            {
                "title": "Clarify outcome",
                "description": "Define the accepted result.",
                "completion_criteria": ["Outcome and constraints are recorded."],
            },
            {
                "title": "Prepare increment",
                "description": "Define the smallest useful increment.",
            },
        ],
    )

    payload = result.to_dict()
    assert payload["metadata"]["planning_boundary"] == "bounded_non_executing"
    assert payload["canonical_plan"]["selection_id"] == "sel_1234567890abcdef"
    assert len(payload["canonical_plan"]["steps"]) == 2
    assert payload["canonical_plan"]["steps"][0]["completion_criteria"] == [
        "Evidence confirms: Define the accepted result."
    ]
