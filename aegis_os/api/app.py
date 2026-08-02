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

from aegis_core.contracts import (
    AuthorityRequirement,
    CapabilitySelection,
    EligibilityState,
    OperationalState,
)
from aegis_os.core.cognitive_runtime import (
    RUNTIME_SCHEMA_VERSION,
    CanonicalRuntimeStatus,
)
from aegis_os.core.runtime_errors import RuntimeIntegrityError
from aegis_os.pipeline.composition import (
    create_default_pipeline,
    create_default_runtime,
    create_governed_runtime,
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
    APPLICATION_VERSION = "0.7.0"

# Source checkouts may coexist with an older editable installation.  The
# repository release version remains authoritative for this service build.
if APPLICATION_VERSION != "0.7.0":
    APPLICATION_VERSION = "0.7.0"


class AnalyzeTaskRequest(BaseModel):
    task: str = Field(min_length=1)

    @field_validator("task")
    @classmethod
    def task_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Task cannot be empty.")
        return value


class GovernedSelectionRequest(BaseModel):
    request_id: str = Field(pattern=r"^req_[A-Za-z0-9]+$")
    capability_id: str = Field(pattern=r"^cap_[A-Za-z0-9_]+$")
    capability_version: str = Field(min_length=1)
    eligibility: EligibilityState = EligibilityState.ELIGIBLE
    rationale: str = Field(min_length=1)
    health_state: OperationalState = OperationalState.HEALTHY
    authority_requirement: AuthorityRequirement = AuthorityRequirement.NONE
    selection_id: str = Field(pattern=r"^sel_[A-Za-z0-9]+$")

    def to_contract(self) -> CapabilitySelection:
        return CapabilitySelection(
            request_id=self.request_id,
            capability_id=self.capability_id,
            capability_version=self.capability_version,
            eligibility=self.eligibility,
            rationale=self.rationale,
            health_state=self.health_state,
            authority_requirement=self.authority_requirement,
            selection_id=self.selection_id,
        )


class GovernedRuntimeApiRequest(BaseModel):
    task: str = Field(min_length=1)
    interpretation_id: str = Field(pattern=r"^int_[A-Za-z0-9]+$")
    selection: GovernedSelectionRequest
    selected_agent: str = Field(min_length=1)
    workflow_definition: list[str] | None = None
    execute: bool = False

    @field_validator("task", "selected_agent")
    @classmethod
    def governed_text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value cannot be blank.")
        return value


create_pipeline = create_default_pipeline
create_runtime = create_default_runtime


def create_app() -> FastAPI:
    application = FastAPI(
        title="AEGIS Platform API",
        version=APPLICATION_VERSION,
    )
    runtime = create_runtime()
    governed_runtime = create_governed_runtime()

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

        if request.url.path in {"/analyze-task", "/execute-task", "/governed-runtime"}:
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

    @application.exception_handler(RuntimeIntegrityError)
    async def runtime_integrity_error(
        request: Request,
        error: RuntimeIntegrityError,
    ) -> JSONResponse:
        request_id = request.state.request_id
        logger.error(
            "event=runtime_integrity_failure request_id=%s code=%s",
            request_id,
            error.error_code,
        )
        return JSONResponse(
            status_code=500,
            content={
                "schema_version": RUNTIME_SCHEMA_VERSION,
                "request_id": request_id,
                "detail": error.to_dict(),
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

    @application.get("/capabilities/status")
    def capability_status() -> dict:
        selector = runtime.pipeline.capability_selector
        ops_selector = getattr(selector, "ops_selector", None)
        diagnostic = getattr(ops_selector, "diagnostic", None)
        return {
            "service": SERVICE_NAME,
            "selection_mode": (
                "live-ops-with-bounded-fallback"
                if ops_selector is not None
                else "platform-internal"
            ),
            "ops": diagnostic,
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
    ):
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
        response_payload = {
            "analysis": analysis_payload,
            "execution": receipt.to_dict(),
            "validation": runtime_result.validation.to_dict(),
            "simulated": runtime_result.simulated,
        }
        if runtime_result.status is CanonicalRuntimeStatus.CONFORMANCE_FAILED:
            return JSONResponse(
                status_code=500,
                content=jsonable_encoder(
                    {
                        **response_payload,
                        "request_id": runtime_result.request_id,
                        "runtime_status": runtime_result.status.value,
                    }
                ),
            )
        return response_payload


    @application.post("/governed-runtime")
    def governed_runtime_endpoint(
        body: GovernedRuntimeApiRequest,
        request: Request,
    ) -> dict:
        """Run the canonical governed pipeline from an explicit selection.

        This endpoint never infers authority and never treats simulation as
        evidence of a real-world effect. Approval-required requests without a
        matching grant stop in the paused state.
        """
        from aegis_os.core.governed_runtime import GovernedRuntimeRequest

        request_id = request.state.request_id
        try:
            result = governed_runtime.process(
                GovernedRuntimeRequest(
                    task=body.task,
                    interpretation_id=body.interpretation_id,
                    selection=body.selection.to_contract(),
                    selected_agent=body.selected_agent,
                    workflow_definition=body.workflow_definition,
                    execute=body.execute,
                )
            )
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

        payload = result.to_dict()
        payload["correlation_id"] = request_id
        logger.info(
            "event=governed_runtime_completed request_id=%s "
            "canonical_request_id=%s runtime_status=%s execution_performed=%s",
            request_id,
            result.request_id,
            result.status.value,
            result.execution_performed,
        )
        return payload

    return application


app = create_app()
