from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

DESCRIPTION_MAX_LENGTH = 16_000


class StartThreatModelRequest(BaseModel):
    id: UUID
    description: Optional[str] = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    title: Optional[str] = None
    application_type: Optional[str] = "hybrid"
    assumptions: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class ThreatItem(BaseModel):
    name: str
    stride_category: str
    description: str
    target: str
    source: str
    likelihood: str
    impact: str
    mitigations: List[str] = Field(min_length=1)
    prerequisites: List[str] = Field(default_factory=list)
    vector: str


class ThreatMutationRequest(BaseModel):
    op: Literal["add", "update", "delete", "replace"]
    threats: List[ThreatItem] = Field(min_length=1)


class ScanFlowRequest(BaseModel):
    source_entity: str
    target_entity: str
    flow_description: str


class ThreatModelStatusResponse(BaseModel):
    id: str
    state: str
    detail: Optional[dict] = None
    updated_at: Optional[str] = None
    retry: int = 0


class ThreatModelListItem(BaseModel):
    id: str
    title: Optional[str] = None
    state: str
    diagram_path: Optional[str] = None
    application_type: Optional[str] = None
    updated_at: Optional[str] = None
    threat_count: Optional[int] = None


class RestoreRequest(BaseModel):
    mode: Literal["replace", "merge"]
    backup: dict
