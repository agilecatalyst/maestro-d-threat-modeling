from typing import Optional

from workflow_graph import pipeline_graph


def run_pipeline(
    job_id: str,
    diagram_path: Optional[str],
    description: Optional[str],
    application_type: Optional[str] = None,
):
    pipeline_graph.invoke(
        {
            "job_id": str(job_id),
            "diagram_path": diagram_path,
            "description": description,
            "application_type": application_type,
        }
    )
