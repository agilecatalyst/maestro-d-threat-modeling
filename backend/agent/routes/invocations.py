from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse
from schemas import InvocationRequest
from pipeline_worker import run_pipeline
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["invocations"])


@router.options("/invocations")
async def options_invocations():
    return JSONResponse(content={"message": "OK"})


@router.post("/invocations", status_code=202)
async def create_invocation(
    request: InvocationRequest,
    background_tasks: BackgroundTasks,
):
    job_id = str(request.input.id)
    logger.info("invocation accepted - job_id: %s", job_id)

    background_tasks.add_task(
        run_pipeline,
        job_id,
        request.input.diagram_path,
        request.input.description,
        request.input.application_type,
    )

    return {
        "statusCode": 202,
        "body": {
            "message": "accepted",
            "job_id": job_id,
        },
    }
