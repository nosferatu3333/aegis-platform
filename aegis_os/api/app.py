from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from aegis_os.agents.agent_profile import AgentProfile
from aegis_os.agents.agent_registry import AgentRegistry
from aegis_os.agents.capability import Capability
from aegis_os.agents.capability_matcher import CapabilityMatcher
from aegis_os.pipeline.agent_selector_adapter import AgentSelectorAdapter
from aegis_os.pipeline.request_pipeline import CognitiveRequestPipeline


API_DIRECTORY = Path(__file__).resolve().parent
STATIC_DIRECTORY = API_DIRECTORY / "static"
TEMPLATE_DIRECTORY = API_DIRECTORY / "templates"


class AnalyzeTaskRequest(BaseModel):
    task: str = Field(min_length=1)


def create_pipeline() -> CognitiveRequestPipeline:
    registry = AgentRegistry()
    registry.register(
        AgentProfile(
            "Research Agent",
            [
                Capability("research"),
                Capability("knowledge"),
            ],
        )
    )
    registry.register(
        AgentProfile(
            "Analysis Agent",
            [
                Capability("analysis"),
                Capability("evaluation"),
            ],
        )
    )

    selector = AgentSelectorAdapter(
        registry=registry,
        matcher=CapabilityMatcher(),
    )
    return CognitiveRequestPipeline(capability_selector=selector)


def create_app() -> FastAPI:
    application = FastAPI(title="AEGIS Platform API")
    pipeline = create_pipeline()

    application.mount(
        "/static",
        StaticFiles(directory=STATIC_DIRECTORY),
        name="static",
    )

    @application.get("/", response_class=FileResponse)
    def dashboard() -> FileResponse:
        return FileResponse(
            TEMPLATE_DIRECTORY / "dashboard.html"
        )

    @application.post("/analyze-task")
    def analyze_task(request: AnalyzeTaskRequest) -> dict:
        try:
            return pipeline.process_task(request.task).to_dict()
        except ValueError as error:
            raise HTTPException(
                status_code=422,
                detail=str(error),
            ) from error

    return application


app = create_app()
