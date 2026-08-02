from fastapi.testclient import TestClient

from aegis_os.api.app import create_app

client = TestClient(create_app())


def payload(*, execute=True, authority="none"):
    return {
        "task": "Perform bounded governed work",
        "interpretation_id": "int_1234567890abcdef",
        "selection": {
            "request_id": "req_1234567890abcdef",
            "capability_id": "cap_iterative_ai_development",
            "capability_version": "0.2.0",
            "eligibility": "eligible",
            "rationale": "Explicit canonical selection supplied by OPS.",
            "health_state": "healthy",
            "authority_requirement": authority,
            "selection_id": "sel_1234567890abcdef",
        },
        "selected_agent": "Execution Agent",
        "workflow_definition": ["Prepare bounded work", "Verify evidence"],
        "execute": execute,
    }


def test_governed_runtime_analysis_only_exposes_canonical_plan():
    response = client.post("/governed-runtime", json=payload(execute=False))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "analyzed"
    assert body["analysis"]["canonical_plan"] is not None
    assert body["authority"] is None
    assert body["execution_performed"] is False
    assert body["correlation_id"]


def test_governed_runtime_completes_unrestricted_simulated_flow():
    response = client.post("/governed-runtime", json=payload())

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["authority"]["ready"] is True
    assert body["execution"]["status"] == "completed"
    assert body["validation"]["status"] == "passed"
    assert body["reconciliation"]["outcome"] == "complete"
    assert body["simulated"] is True


def test_governed_runtime_pauses_when_approval_is_required():
    response = client.post(
        "/governed-runtime",
        json=payload(authority="approval_required"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "paused"
    assert body["authority"]["paused"] is True
    assert body["execution"] is None
    assert body["execution_performed"] is False


def test_governed_runtime_rejects_noncanonical_selection_identifiers():
    invalid = payload()
    invalid["selection"]["request_id"] = "not-canonical"

    response = client.post("/governed-runtime", json=invalid)

    assert response.status_code == 422
