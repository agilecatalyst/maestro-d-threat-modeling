import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

from flow_scan_worker import scan_flow_threats

logger = logging.getLogger(__name__)

router = APIRouter(tags=["scan-flow"])


class FlowPayload(BaseModel):
    source_entity: str
    target_entity: str
    flow_description: str


class ScanFlowRequest(BaseModel):
    summary: str = ""
    assets: list = Field(default_factory=list)
    flow: FlowPayload
    threat_sources: list = Field(default_factory=list)


@router.post("/scan-flow")
def scan_flow(request: ScanFlowRequest):
    threats = scan_flow_threats(
        request.summary,
        request.assets,
        request.flow.model_dump(),
        request.threat_sources,
    )
    return {"threats": threats, "count": len(threats)}
