from fastapi.testclient import TestClient

from aegis_os.api.app import create_app


client = TestClient(create_app())


def test_dashboard_serves_mission_interface():
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "AEGIS" in response.text
    assert 'id="mission-task"' in response.text
    assert "Analyze Mission" in response.text
    assert 'data-endpoint="/analyze-task"' in response.text
    assert "not yet autonomously" in response.text


def test_dashboard_and_api_support_research_mission_flow():
    dashboard = client.get("/")
    analysis = client.post(
        "/analyze-task",
        json={
            "task": (
                "Research competitors in the "
                "cognitive systems market"
            )
        },
    )

    assert dashboard.status_code == 200
    assert analysis.status_code == 200

    payload = analysis.json()

    assert payload["capability"]["name"] == "Research Agent"
    assert "research" in payload["intent"]["required_capabilities"]
    assert [
        step["order"]
        for step in payload["workflow"]
    ] == sorted(
        step["order"]
        for step in payload["workflow"]
    )
