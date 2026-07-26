from fastapi.testclient import TestClient

from aegis_os.api.app import create_app


client = TestClient(create_app())


def test_analyze_task_uses_real_research_profile():
    response = client.post(
        "/analyze-task",
        json={
            "task": (
                "Research competitors in the "
                "cognitive systems market"
            )
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["capability"]["name"] == "Research Agent"
    assert "research" in payload["intent"]["required_capabilities"]
    assert payload["workflow"]


def test_analyze_task_rejects_empty_task():
    response = client.post(
        "/analyze-task",
        json={"task": "   "},
    )

    assert response.status_code == 422


def test_analyze_task_rejects_invalid_body():
    missing_task = client.post(
        "/analyze-task",
        json={},
    )
    invalid_body = client.post(
        "/analyze-task",
        json={"task": ["research"]},
    )

    assert missing_task.status_code == 422
    assert invalid_body.status_code == 422
