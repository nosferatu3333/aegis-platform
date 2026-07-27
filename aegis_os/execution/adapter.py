from __future__ import annotations

import logging
from typing import Any

from aegis_os.execution.models import ExecutionRequest
from aegis_os.pipeline.models import CognitiveRequestResult, PipelineStatus


logger = logging.getLogger("aegis.execution")


def build_execution_request(
    cognitive_result: CognitiveRequestResult,
    request_id: str,
    *,
    constraints: list[str] | None = None,
    permissions: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> ExecutionRequest:
    if cognitive_result.status is not PipelineStatus.READY:
        raise ValueError("Cognitive result is not ready for execution.")

    request = ExecutionRequest(
        request_id=request_id,
        mission=cognitive_result.task,
        selected_agent=cognitive_result.capability.name,
        required_capabilities=list(
            cognitive_result.intent.required_capabilities
        ),
        workflow_steps=sorted(
            cognitive_result.workflow,
            key=lambda step: step.order,
        ),
        constraints=list(constraints or []),
        permissions=list(permissions or []),
        metadata={
            "analysis_schema_version": cognitive_result.schema_version,
            **(metadata or {}),
        },
    )
    logger.info(
        "event=execution_request_created request_id=%s "
        "selected_agent=%s simulated=true",
        request.request_id,
        request.selected_agent,
    )
    return request
