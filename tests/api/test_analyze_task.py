import logging

from fastapi.testclient import TestClient

from aegis_os.api.app import create_app

client = TestClient(create_app())


def test_analyze_task_uses_real_research_profile(caplog):
    caplog.set_level(logging.INFO, logger="aegis.api")

    response = client.post(
        "/analyze-task",
        headers={"X-Request-ID": "research-test-001"},
        json={"task": ("Research competitors in the cognitive systems market")},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["schema_version"] == "1.0"
    assert payload["request_id"] == "research-test-001"
    assert response.headers["X-Request-ID"] == "research-test-001"
    assert payload["capability"]["name"] == "Research Agent"
    assert "research" in payload["intent"]["required_capabilities"]
    assert payload["workflow"]
    assert "event=request_received request_id=research-test-001" in caplog.text
    assert "primary_intent=research" in caplog.text
    assert "required_capabilities=['research']" in caplog.text
    assert "selected_profile=Research Agent" in caplog.text
    assert "pipeline_status=ready" in caplog.text


def test_analyze_task_uses_real_analysis_profile():
    response = client.post(
        "/analyze-task",
        json={"task": "Analyze market risks and trends"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["capability"]["name"] == "Analysis Agent"
    assert "analysis" in payload["intent"]["required_capabilities"]
    assert payload["status"] == "ready"


def test_analyze_task_returns_explicit_no_match_result():
    response = client.post(
        "/analyze-task",
        json={"task": "Plan a product launch roadmap"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "failed"
    assert payload["capability"]["capability_id"] == "unknown"
    assert payload["workflow"] == []
    assert payload["metadata"]["failure_code"] == "no_capability_match"
    assert payload["metadata"]["failure_reason"]
    assert payload["request_id"]


def test_analyze_task_rejects_empty_task():
    response = client.post(
        "/analyze-task",
        json={"task": "   "},
    )

    assert response.status_code == 422
    assert response.json()["schema_version"] == "1.0"
    assert response.json()["request_id"]


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
    assert missing_task.json()["request_id"]
    assert invalid_body.json()["request_id"]


def test_health_reports_pipeline_availability():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "aegis-platform",
        "status": "ok",
        "version": "0.1.0",
        "pipeline_available": True,
    }
