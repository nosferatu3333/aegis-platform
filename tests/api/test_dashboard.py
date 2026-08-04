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
    assert "Simulate Execution" in response.text
    assert "Run Governed Demo" in response.text
    assert 'data-endpoint="/governed-runtime"' in response.text
    assert 'id="governed-panel"' in response.text
    assert "DEMONSTRATION SURFACE" in response.text
    assert 'data-endpoint="/analyze-task"' in response.text
    assert 'data-endpoint="/execute-task"' in response.text
    assert "SIMULATED EXECUTION ONLY" in response.text
    assert "not yet autonomously" in response.text
    assert 'id="validation-panel"' in response.text
    assert 'id="validation-status"' in response.text
    assert 'id="operation-outcome"' in response.text
    assert 'id="validation-checks"' in response.text
    assert 'id="validation-evidence"' in response.text
    assert "Runtime validation" in response.text
    assert "CONFORMANCE ONLY" in response.text
    assert "not mission success" in response.text
    assert "quality evaluation" in response.text
    assert "governance approval" in response.text
    assert "execution authorization" in response.text


def test_dashboard_and_api_support_research_mission_flow():
    dashboard = client.get("/")
    analysis = client.post(
        "/analyze-task",
        json={"task": ("Research competitors in the cognitive systems market")},
    )

    assert dashboard.status_code == 200
    assert analysis.status_code == 200

    payload = analysis.json()

    assert payload["capability"]["name"] == "Research Agent"
    assert "research" in payload["intent"]["required_capabilities"]
    assert [step["order"] for step in payload["workflow"]] == sorted(
        step["order"] for step in payload["workflow"]
    )


def test_dashboard_script_renders_validation_separately_from_execution():
    response = client.get("/static/dashboard.js")

    assert response.status_code == 200
    assert "function renderExecution(receipt)" in response.text
    assert "function renderValidation(validation)" in response.text
    assert "payload.validation" in response.text
    assert '"#operation-outcome"' in response.text
    assert '"#validation-checks"' in response.text
    assert '"#validation-evidence"' in response.text


def test_dashboard_script_exposes_governed_runtime_demo_separately():
    response = client.get("/static/dashboard.js")

    assert response.status_code == 200
    assert "function buildGovernedRequest()" in response.text
    assert "function renderGoverned(payload)" in response.text
    assert 'governedButton.dataset.endpoint' in response.text
    assert "authority_requirement: authorityRequirement.value" in response.text
    assert '"#reconciliation-outcome"' in response.text

def test_dashboard_documents_operator_lifecycle() -> None:
    from pathlib import Path

    repository_root = Path(__file__).resolve().parents[2]
    dashboard = (
        repository_root
        / "aegis_os"
        / "api"
        / "templates"
        / "dashboard.html"
    ).read_text(encoding="utf-8")

    assert 'id="operator-lifecycle"' in dashboard
    assert 'id="operator-start-command"' in dashboard
    assert "python -m aegis_os serve" in dashboard
    assert 'id="operator-stop-command"' in dashboard
    assert "Ctrl+C" in dashboard
    assert 'id="operator-shutdown-guidance"' in dashboard
    assert "does not expose a remote shutdown endpoint" in dashboard


def test_dashboard_governed_request_preserves_required_contract() -> None:
    from pathlib import Path

    repository_root = Path(__file__).resolve().parents[2]
    script = (
        repository_root
        / "aegis_os"
        / "api"
        / "static"
        / "dashboard.js"
    ).read_text(encoding="utf-8")

    required_fragments = (
        "function buildGovernedRequest()",
        "interpretation_id:",
        "request_id:",
        "capability_id:",
        "capability_version:",
        "rationale:",
        "selection_id:",
        "selected_agent:",
        "authority_requirement:",
    )

    for fragment in required_fragments:
        assert fragment in script

    assert '"#authority-outcome"' in script
    assert '"#verdict-reason"' in script
