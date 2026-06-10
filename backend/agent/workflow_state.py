from typing import Optional, TypedDict


class PipelineState(TypedDict):
    job_id: str
    diagram_path: Optional[str]
    description: Optional[str]
    application_type: Optional[str]
