from aegis_os.operator import build_operator_readiness, port_available


def test_operator_readiness_preserves_release_limitations(monkeypatch):
    monkeypatch.setattr("aegis_os.operator.port_available", lambda host, port: True)
    readiness = build_operator_readiness()
    assert readiness.status in {"ready", "blocked"}
    assert readiness.endpoint == "http://127.0.0.1:8000"
    assert "deterministic simulation" in readiness.limitations[0]
    assert readiness.diagnostics["platform_version"] == readiness.platform_version


def test_unavailable_port_blocks_readiness(monkeypatch):
    monkeypatch.setattr("aegis_os.operator.port_available", lambda host, port: False)
    readiness = build_operator_readiness(port=8765)
    assert readiness.status == "blocked"
    assert readiness.port == 8765


def test_port_available_returns_boolean():
    assert isinstance(port_available("127.0.0.1", 0), bool)
