import logging
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from chat import clear_session, run_chat
from models import InvocationRequest
from prompt import context_from_input
from security import parse_cors_origins

logger = logging.getLogger(__name__)

app = FastAPI(title="Maestro'D Sentry", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_origins(os.getenv("CORS_ORIGINS")),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def _session_ids(http_request: Request, input_data: dict) -> tuple[str, str]:
    header = http_request.headers.get("X-Session-Id") or http_request.headers.get(
        "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id"
    )
    threat_model_id = (
        input_data.get("threat_model_id")
        or input_data.get("threatModelId")
        or (header.split("/")[0] if header and "/" in header else header)
    )
    if not threat_model_id:
        raise HTTPException(status_code=400, detail="Missing threat_model_id or X-Session-Id header")
    session_id = header or threat_model_id
    return session_id, str(threat_model_id)


@app.get("/ping")
async def ping():
    return {"status": "Healthy", "service": "maestro-d-sentry"}


@app.options("/invocations")
async def options_invocations():
    return {"message": "OK"}


@app.post("/invocations")
async def invocations(request: InvocationRequest, http_request: Request):
    input_data = request.input
    request_type = input_data.get("type")

    if request_type == "ping":
        return {"type": "pong", "message": "pong"}

    session_id, threat_model_id = _session_ids(http_request, input_data)

    if request_type == "clear" or request_type == "delete_history":
        clear_session(session_id, threat_model_id)
        return {"type": "clear_complete", "message": "Session cleared"}

    if request_type == "history":
        return {"type": "history", "messages": []}

    message = (
        input_data.get("message")
        or input_data.get("prompt")
        or input_data.get("text")
    )
    if not message:
        raise HTTPException(status_code=400, detail="Missing message in input")

    context = context_from_input(input_data)
    try:
        result = run_chat(session_id, threat_model_id, message, context)
    except Exception as exc:
        logger.exception("Sentry chat failed")
        return JSONResponse(
            status_code=500,
            content={"type": "error", "error": str(exc)},
        )

    return result
