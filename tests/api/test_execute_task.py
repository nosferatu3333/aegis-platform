from importlib import import_module

from fastapi.testclient import TestClient

from aegis_os.api.app import create_app
from aegis_os.pipeline.composition import create_default_runtime

api_app = import_module("aegis_os.api.app")

client = TestClient(create_app())
MISSION = "Research competitors in the cognitive systems market"


def test_execute_task_runs_simulated_workflow():
    response = client.post("/execute-task", json={"task": MISSION})

    assert response.status_code == 200
    payload = response.json()
    analysis = payload["analysis"]
    execution = payload["execution"]

    assert analysis["capability"]["name"] == "Research Agent"
    assert execution["selected_agent"] == "Research Agent"
    assert execution["status"] == "completed"
    assert [step["order"] for step in execution["steps"]] == [
        1,
        2,
        3,
        4,
        5,
    ]
    assert all(step["status"] == "completed" for step in execution["steps"])
    assert execution["completed_steps"] == 5
    assert execution["simulated"] is True
    assert payload["simulated"] is True


def test_execute_task_rejects_invalid_task():
    response = client.post("/execute-task", json={"task": "   "})

    assert response.status_code == 422


def test_analyze_task_contract_remains_analysis_only():
    response = client.post("/analyze-task", json={"task": MISSION})

    assert response.status_code == 200
    payload = response.json()
    assert payload["capability"]["name"] == "Research Agent"
    assert "analysis" not in payload
    assert "execution" not in payload


def test_api_routes_delegate_to_canonical_runtime(monkeypatch):
    runtime = create_default_runtime()
    calls = []
    original_run = runtime.run

    def record_run(task, request_id, *, execute=False):
        calls.append(execute)
        return original_run(task, request_id, execute=execute)

    runtime.run = record_run
    monkeypatch.setattr(api_app, "create_runtime", lambda: runtime)
    delegated_client = TestClient(api_app.create_app())

    analysis_response = delegated_client.post(
        "/analyze-task",
        json={"task": MISSION},
    )
    execution_response = delegated_client.post(
        "/execute-task",
        json={"task": MISSION},
    )

    assert analysis_response.status_code == 200
    assert execution_response.status_code == 200
    assert calls == [False, True]
