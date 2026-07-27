from aegis_os.execution.models import (
    ExecutionReceipt,
    ExecutionRequest,
    ExecutionStep,
)


def test_execution_models_construct_and_serialize():
    request = ExecutionRequest(
        request_id="request-1",
        mission="Research a market",
        selected_agent="Research Agent",
        required_capabilities=["research"],
        workflow_steps=[{"order": 1, "description": "Gather inputs"}],
    )
    receipt = ExecutionReceipt(
        request_id=request.request_id,
        mission=request.mission,
        selected_agent=request.selected_agent,
        steps=[
            ExecutionStep(
                step_id="step-1",
                order=1,
                description="Gather inputs",
            )
        ],
    )

    assert request.to_dict()["required_capabilities"] == ["research"]
    assert receipt.to_dict()["status"] == "pending"
    assert receipt.to_dict()["steps"][0]["status"] == "pending"
    assert receipt.to_dict()["schema_version"] == "1.0"
    assert receipt.to_dict()["simulated"] is True


def test_execution_models_have_safe_mutable_defaults():
    first = ExecutionRequest("one", "Mission", "Agent")
    second = ExecutionRequest("two", "Mission", "Agent")
    first.metadata["changed"] = True
    first.permissions.append("simulation")

    first_receipt = ExecutionReceipt("one", "Mission", "Agent")
    second_receipt = ExecutionReceipt("two", "Mission", "Agent")
    first_receipt.logs.append("changed")

    assert second.metadata == {}
    assert second.permissions == []
    assert second_receipt.logs == []
