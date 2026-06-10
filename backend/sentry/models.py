from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ThreatRecord(BaseModel):
    name: str
    stride_category: str
    description: str
    target: str
    source: str
    likelihood: Literal["Low", "Medium", "High"] = "Medium"
    impact: str
    mitigations: List[str] = Field(min_length=1)
    prerequisites: List[str] = Field(default_factory=list)
    vector: str


class InvocationRequest(BaseModel):
    input: Dict[str, Any]


class ChatResponse(BaseModel):
    type: str = "message"
    reply: str
    tools_used: List[str] = Field(default_factory=list)
