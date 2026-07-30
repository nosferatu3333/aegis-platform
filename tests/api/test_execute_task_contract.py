from fastapi.testclient import TestClient

from aegis_os.api.app import create_app

client = TestClient(create_app())
MISSION = "Research competitors in the cognitive systems market"
REQUEST_ID = "api-compatibility-1"

LEGACY_RESPONSE_FIELDS = {
    "analysis",
    "execution",
    "simulated",
}
LEGACY_EXECUTION_FIELDS = {
    "request_id",
    "mission",
    "selected_agent",
    "status",
    "steps",
    "started_at",
    "finished_at",
    "completed_steps",
    "failed_steps",
    "logs",
    "simulated",
    "schema_version",
}


def test_execute_task_validation_is_additive_under_schema_version_one():
    response = client.post(
        "/execute-task",
        json={"task": MISSION},
        headers={"X-Request-ID": REQUEST_ID},
    )

    assert response.status_code == 200
    payload = response.json()
    assert LEGACY_RESPONSE_FIELDS <= payload.keys()
    assert set(payload) - LEGACY_RESPONSE_FIELDS == {"validation"}
    assert payload["execution"]["schema_version"] == "1.0"
    assert payload["validation"]["schema_version"] == "1.0"


def test_typed_execution_mode_is_additive_to_legacy_receipt():
    response = client.post(
        "/execute-task",
        json={"task": MISSION},
        headers={"X-Request-ID": REQUEST_ID},
    )

    execution = response.json()["execution"]
    assert LEGACY_EXECUTION_FIELDS <= execution.keys()
    assert set(execution) - LEGACY_EXECUTION_FIELDS == {"execution_mode"}
    assert execution["execution_mode"] == "simulated"
    assert execution["simulated"] is True


def test_execute_task_preserves_analysis_contract_exactly():
    analysis_response = client.post(
        "/analyze-task",
        json={"task": MISSION},
        headers={"X-Request-ID": REQUEST_ID},
    )
    execution_response = client.post(
        "/execute-task",
        json={"task": MISSION},
        headers={"X-Request-ID": REQUEST_ID},
    )

    assert analysis_response.status_code == 200
    assert execution_response.status_code == 200
    assert execution_response.json()["analysis"] == analysis_response.json()
