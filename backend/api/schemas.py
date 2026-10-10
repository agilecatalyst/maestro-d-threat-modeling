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


ProviderKind = Literal["openai_compatible", "openai", "anthropic", "gemini"]
ProviderRole = Literal["threats", "sentry"]


class LlmProviderProfileRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    kind: ProviderKind
    base_url: Optional[str] = Field(default=None, max_length=512)
    model: str = Field(min_length=1, max_length=256)
    api_key_env: Optional[str] = Field(default=None, max_length=128)
    temperature: Optional[float] = None
    max_tokens: Optional[int] = Field(default=None, ge=1)
    timeout_sec: int = Field(default=180, ge=1, le=3600)

    model_config = ConfigDict(extra="forbid", protected_namespaces=())


class LlmProviderProfileResponse(BaseModel):
    id: str
    name: str
    kind: str
    base_url: Optional[str] = None
    model: str
    api_key_env: Optional[str] = None
    key_present: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout_sec: int = 180
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(protected_namespaces=())


class LlmRoleBindingRequest(BaseModel):
    profile_id: UUID

    model_config = ConfigDict(extra="forbid")


class ResolvedProviderConfigResponse(BaseModel):
    role: str
    kind: str
    model: str
    base_url: Optional[str] = None
    api_key_env: Optional[str] = None
    key_present: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout_sec: float = 180.0
    source: Literal["db", "env"] = "env"

    model_config = ConfigDict(protected_namespaces=())


class LlmProviderTestResponse(BaseModel):
    ok: bool
    latency_ms: int
    detail: Optional[str] = None
    error: Optional[str] = None
