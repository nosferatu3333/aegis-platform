import logging
import re
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from aegis_os.pipeline.composition import (
    create_default_pipeline,
    create_default_runtime,
)
from aegis_os.pipeline.models import SCHEMA_VERSION

API_DIRECTORY = Path(__file__).resolve().parent
STATIC_DIRECTORY = API_DIRECTORY / "static"
TEMPLATE_DIRECTORY = API_DIRECTORY / "templates"
SERVICE_NAME = "aegis-platform"
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
logger = logging.getLogger("aegis.api")
logger.setLevel(logging.INFO)

try:
    APPLICATION_VERSION = version("aegis-os")
except PackageNotFoundError:
    APPLICATION_VERSION = "0.1.0"


class AnalyzeTaskRequest(BaseModel):
    task: str = Field(min_length=1)

    @field_validator("task")
    @classmethod
    def task_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Task cannot be empty.")
        return value


create_pipeline = create_default_pipeline
create_runtime = create_default_runtime


def create_app() -> FastAPI:
    application = FastAPI(
        title="AEGIS Platform API",
        version=APPLICATION_VERSION,
    )
    runtime = create_runtime()

    @application.middleware("http")
    async def correlate_request(
        request: Request,
        call_next,
    ) -> Response:
        supplied_request_id = request.headers.get("X-Request-ID", "")
        request_id = (
            supplied_request_id
            if REQUEST_ID_PATTERN.fullmatch(supplied_request_id)
            else str(uuid4())
        )
        request.state.request_id = request_id

        if request.url.path in {"/analyze-task", "/execute-task"}:
            logger.info(
                "event=request_received request_id=%s",
                request_id,
            )

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @application.exception_handler(RequestValidationError)
    async def request_validation_error(
        request: Request,
        error: RequestValidationError,
    ) -> JSONResponse:
        request_id = request.state.request_id
        logger.info(
            "event=request_rejected request_id=%s pipeline_status=invalid_request",
            request_id,
        )
        return JSONResponse(
            status_code=422,
            content={
                "schema_version": SCHEMA_VERSION,
                "request_id": request_id,
                "detail": jsonable_encoder(error.errors()),
            },
        )

    application.mount(
        "/static",
        StaticFiles(directory=STATIC_DIRECTORY),
        name="static",
    )

    @application.get("/", response_class=FileResponse)
    def dashboard() -> FileResponse:
        return FileResponse(TEMPLATE_DIRECTORY / "dashboard.html")

    @application.get("/health")
    def health() -> dict:
        return {
            "service": SERVICE_NAME,
            "status": "ok",
            "version": APPLICATION_VERSION,
            "pipeline_available": runtime.pipeline is not None,
        }

    @application.post("/analyze-task")
    def analyze_task(
        body: AnalyzeTaskRequest,
        request: Request,
    ) -> dict:
        request_id = request.state.request_id
        try:
            runtime_result = runtime.run(
                body.task,
                request_id,
                execute=False,
            )
        except ValueError as error:
            logger.info(
                "event=request_rejected request_id=%s pipeline_status=invalid_request",
                request_id,
            )
            raise HTTPException(
                status_code=422,
                detail=str(error),
            ) from error

        result = runtime_result.analysis
        payload = result.to_dict()
        payload["request_id"] = request_id

        selected_profile = (
            result.capability.name if result.status.value != "failed" else "none"
        )
        logger.info(
            "event=analysis_completed request_id=%s "
            "primary_intent=%s required_capabilities=%s "
            "selected_profile=%s pipeline_status=%s",
            request_id,
            result.intent.primary_intent,
            list(result.intent.required_capabilities),
            selected_profile,
            result.status.value,
        )
        return payload

    @application.post("/execute-task")
    def execute_task(
        body: AnalyzeTaskRequest,
        request: Request,
    ) -> dict:
        request_id = request.state.request_id
        try:
            runtime_result = runtime.run(
                body.task,
                request_id,
                execute=True,
            )
        except ValueError as error:
            logger.info(
                "event=request_rejected request_id=%s pipeline_status=invalid_request",
                request_id,
            )
            raise HTTPException(
                status_code=422,
                detail=str(error),
            ) from error

        analysis = runtime_result.analysis
        receipt = runtime_result.execution
        if receipt is None:
            raise HTTPException(
                status_code=422,
                detail=("Cognitive result is not ready for execution."),
            )
        analysis_payload = analysis.to_dict()
        analysis_payload["request_id"] = request_id
        return {
            "analysis": analysis_payload,
            "execution": receipt.to_dict(),
            "simulated": runtime_result.simulated,
        }

    return application


app = create_app()
