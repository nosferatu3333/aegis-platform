from pathlib import Path

import pytest

from aegis_os.pipeline.agent_selector_adapter import AgentSelectorAdapter
from aegis_os.pipeline.ops_capability_adapter import (
    HybridCapabilitySelector,
    OpsCapabilitySelectorAdapter,
    OpsIntegrationError,
)
from aegis_os.pipeline.request_pipeline import CognitiveRequestPipeline


OPS_ROOT = Path(__file__).resolve().parents[4] / "ops"


def test_live_ops_selects_real_capability_and_workflow():
    selector = OpsCapabilitySelectorAdapter(OPS_ROOT)
    pipeline = CognitiveRequestPipeline(selector)

    result = pipeline.process_task(
        "Build an AI software feature iteratively and review each increment"
    )

    assert result.capability.capability_id == (
        "aegis.capability.iterative_ai_development"
    )
    assert result.capability.score > 0
    assert result.metadata["capability_source"] == "aegis-ops"
    assert result.metadata["capability_source_path"] == str(OPS_ROOT.resolve())
    assert len(result.workflow) == 8
    assert result.workflow[0].title == (
        "Express the desired outcome in user-facing terms."
    )


def test_live_ops_reports_missing_repository():
    selector = OpsCapabilitySelectorAdapter(OPS_ROOT / "missing")

    with pytest.raises(OpsIntegrationError, match="does not exist"):
        selector.select("Build software")

    assert selector.diagnostic["available"] is False
    assert selector.diagnostic["error"]


def test_hybrid_selector_falls_back_when_ops_has_no_positive_match():
    class NoMatchOps:
        def select(self, task, **context):
            return None

    class Fallback:
        def select(self, task, **context):
            return {"capability": {"id": "fallback", "name": "Fallback"}}

    hybrid = HybridCapabilitySelector(NoMatchOps(), Fallback())

    assert hybrid.select("unmatched")["capability"]["id"] == "fallback"


def test_hybrid_selector_falls_back_when_ops_is_unavailable():
    class BrokenOps:
        def select(self, task, **context):
            raise OpsIntegrationError("offline")

    class Fallback:
        def select(self, task, **context):
            return "fallback"

    assert HybridCapabilitySelector(BrokenOps(), Fallback()).select("task") == (
        "fallback"
    )
