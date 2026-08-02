from fastapi.testclient import TestClient

from aegis_os.api.app import create_app

client = TestClient(create_app())


def test_demo_scenarios_expose_bounded_operator_examples():
    response = client.get("/demo/scenarios")
    assert response.status_code == 200
    payload = response.json()
    assert payload["platform_version"] == "1.6.0"
    assert payload["execution_boundary"] == "deterministic simulation only"
    assert {item["expected_outcome"] for item in payload["scenarios"]} == {
        "completed", "paused", "analyzed"
    }


def test_dashboard_presents_seven_stage_operator_journey():
    response = client.get("/")
    assert response.status_code == 200
    for label in ("01 Request", "02 Capability", "03 Plan", "04 Authority", "05 Execution", "06 Evidence", "07 Verdict"):
        assert label in response.text
    assert 'id="operator-verdict"' in response.text
    assert 'id="audit-identifiers"' in response.text


def test_dashboard_exposes_live_ops_selection_evidence():
    response = client.get("/")
    assert 'id="ops-status"' in response.text
    assert 'id="capability-source"' in response.text
    assert 'id="selection-rationale"' in response.text


def test_dashboard_authority_control_never_fabricates_approval():
    response = client.get("/")
    assert 'value="approval_required"' in response.text
    assert "never fabricates a grant" in response.text
    script = client.get("/static/dashboard.js").text
    assert "authority_requirement: authorityRequirement.value" in script
    assert "approval_required" not in script or "authorityRequirement" in script


def test_dashboard_script_maps_runtime_states_to_operator_verdicts():
    script = client.get("/static/dashboard.js").text
    assert 'completed: ["ACCEPTED"' in script
    assert 'paused: ["AWAITING AUTHORITY"' in script
    assert 'denied: ["REJECTED"' in script
    assert 'conformance_failed: ["REJECTED"' in script
    assert 'renderChips("#audit-identifiers"' in script
