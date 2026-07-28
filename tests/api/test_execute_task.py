from fastapi.testclient import TestClient

from aegis_os.api.app import create_app

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
