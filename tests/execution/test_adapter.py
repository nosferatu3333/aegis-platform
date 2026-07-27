from aegis_os.execution.adapter import build_execution_request
from aegis_os.pipeline.intent_analyzer import IntentAnalyzer
from aegis_os.pipeline.models import (
    CapabilityMatch,
    CognitiveRequestResult,
    WorkflowStep,
)


def test_cognitive_result_converts_without_reanalysis():
    result = CognitiveRequestResult(
        task="Research competitors",
        intent=IntentAnalyzer().analyze("Research competitors"),
        capability=CapabilityMatch(
            capability_id="research-agent",
            name="Research Agent",
            confidence=0.9,
            score=9,
        ),
        workflow=[
            WorkflowStep(2, "Compare", "Compare findings"),
            WorkflowStep(1, "Collect", "Collect findings"),
        ],
    )

    request = build_execution_request(result, "request-1")

    assert request.mission == "Research competitors"
    assert request.selected_agent == "Research Agent"
    assert request.required_capabilities == ["research"]
    assert [step.order for step in request.workflow_steps] == [1, 2]
