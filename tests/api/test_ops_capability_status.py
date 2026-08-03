from fastapi.testclient import TestClient

from aegis_os.api.app import create_app


def test_capability_status_exposes_live_ops_diagnostic(monkeypatch, tmp_path):
    monkeypatch.setenv("AEGIS_OPS_PATH", str(tmp_path / "missing-ops"))
    client = TestClient(create_app())

    response = client.get("/capabilities/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["selection_mode"] == "live-ops-with-bounded-fallback"
    assert payload["ops"]["source"] == "aegis-ops"
    assert payload["ops"]["available"] is False
    assert payload["ops"]["error"]
