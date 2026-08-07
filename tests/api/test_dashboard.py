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

def test_dashboard_html_ids_are_unique() -> None:
    import re
    from collections import Counter
    from pathlib import Path

    repository_root = Path(__file__).resolve().parents[2]
    dashboard = (
        repository_root
        / "aegis_os"
        / "api"
        / "templates"
        / "dashboard.html"
    ).read_text(encoding="utf-8")

    identifiers = re.findall(r'id="([^"]+)"', dashboard)
    counts = Counter(identifiers)
    duplicates = {
        identifier: count
        for identifier, count in counts.items()
        if count > 1
    }

    assert duplicates == {}


def test_dashboard_preserves_single_validation_evidence_surface() -> None:
    from pathlib import Path

    repository_root = Path(__file__).resolve().parents[2]
    dashboard = (
        repository_root
        / "aegis_os"
        / "api"
        / "templates"
        / "dashboard.html"
    ).read_text(encoding="utf-8")

    required_singletons = (
        'id="validation-panel"',
        'id="validation-status"',
        'id="operation-outcome"',
        'id="validation-count"',
        'id="validation-checks"',
        'id="validation-evidence"',
        'id="validation-json"',
    )

    for fragment in required_singletons:
        assert dashboard.count(fragment) == 1

    assert "06 / Evidence" in dashboard
    assert "Runtime validation" in dashboard
    assert "CONFORMANCE ONLY" in dashboard
    assert "not mission success" in dashboard
    assert "execution authorization" in dashboard

def test_dashboard_exposes_canonical_demo_contract() -> None:
    from pathlib import Path

    repository_root = Path(__file__).resolve().parents[2]
    dashboard = (
        repository_root
        / "aegis_os"
        / "api"
        / "templates"
        / "dashboard.html"
    ).read_text(encoding="utf-8")

    assert 'id="canonical-demo-guide"' in dashboard
    assert 'id="active-demo-boundary"' in dashboard

    required_demo_labels = (
        "DEMO-A",
        "Research / Analysis",
        "DEMO-B",
        "Bounded Simulation",
        "DEMO-C",
        "Approval Gate",
    )

    for fragment in required_demo_labels:
        assert fragment in dashboard

    assert "Capability ≠ authority" in dashboard
    assert "Plan ≠ approval" in dashboard
    assert "Simulation ≠ real execution" in dashboard
    assert "Validation ≠ permission" in dashboard


def test_dashboard_script_maps_backend_scenarios_to_canonical_demos() -> None:
    from pathlib import Path

    repository_root = Path(__file__).resolve().parents[2]
    script = (
        repository_root
        / "aegis_os"
        / "api"
        / "static"
        / "dashboard.js"
    ).read_text(encoding="utf-8")

    required_mappings = (
        '"analysis-only-research"',
        'code: "DEMO-A"',
        '"live-ops-development"',
        'code: "DEMO-B"',
        '"approval-gated-change"',
        'code: "DEMO-C"',
    )

    for fragment in required_mappings:
        assert fragment in script

    assert "canonicalScenarioPresentation" in script
    assert "applyScenarioPolicy(scenario)" in script
    assert "button.dataset.demoId = presentation.code" in script


def test_canonical_demo_policies_preserve_execution_boundaries() -> None:
    from pathlib import Path

    repository_root = Path(__file__).resolve().parents[2]
    script = (
        repository_root
        / "aegis_os"
        / "api"
        / "static"
        / "dashboard.js"
    ).read_text(encoding="utf-8")

    assert 'boundary: "Analysis only · no execution requested"' in script
    assert "allowDirectSimulation: false" in script
    assert "governedExecute: false" in script

    assert (
        'boundary: "Deterministic simulated execution · no external effect"'
        in script
    )

    assert (
        'boundary: "Approval required · must pause without an explicit grant"'
        in script
    )

    assert (
        "canonicalScenarioPresentation[selectedScenario.id].governedExecute"
        in script
    )


def test_demonstration_baseline_documents_complete_operator_journey() -> None:
    from pathlib import Path

    repository_root = Path(__file__).resolve().parents[2]
    document = (
        repository_root
        / "docs"
        / "mvp"
        / "demonstration-baseline.md"
    ).read_text(encoding="utf-8")

    for step in range(1, 13):
        assert f"{step}." in document

    assert "DEMO-A — Research / Analysis" in document
    assert "DEMO-B — Bounded Simulation" in document
    assert "DEMO-C — Approval Gate" in document
    assert "`execute = false`" in document
    assert "`approval_required`" in document
    assert "Simulation only." in document
    assert "does not claim autonomous real-world execution" in document
