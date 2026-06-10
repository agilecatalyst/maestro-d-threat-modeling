from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from uuid import UUID

class InvocationInput(BaseModel):
    id: UUID
    description: Optional[str] = None
    assumptions: List[str] = []
    application_type: Optional[str] = None
    diagram_path: Optional[str] = None

    model_config = ConfigDict(extra="allow")

class InvocationRequest(BaseModel):
    input: InvocationInput