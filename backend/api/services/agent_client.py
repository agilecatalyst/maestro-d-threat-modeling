import os
from typing import Optional

import httpx

THREAT_DESIGNER_URL = os.getenv("THREAT_DESIGNER_URL", "http://tm-agent:8080")


def invoke_agent(
    job_id: str,
    diagram_path: Optional[str],
    description: Optional[str],
    application_type: Optional[str] = None,
) -> None:
    payload = {
        "input": {
            "id": job_id,
            "diagram_path": diagram_path,
            "description": description or "",
            "application_type": application_type,
        }
    }
    try:
        httpx.post(
            f"{THREAT_DESIGNER_URL}/invocations",
            json=payload,
            timeout=10.0,
        )
    except httpx.TimeoutException:
        pass
    except httpx.RequestError as exc:
        raise RuntimeError(f"Could not reach threat-designer agent: {exc}") from exc


def scan_flow_agent(
    summary: str,
    assets: list,
    flow: dict,
    threat_sources: list,
) -> dict:
    payload = {
        "summary": summary,
        "assets": assets,
        "flow": flow,
        "threat_sources": threat_sources,
    }
    try:
        response = httpx.post(
            f"{THREAT_DESIGNER_URL}/scan-flow",
            json=payload,
            timeout=180.0,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"Flow scan failed: {exc.response.text}") from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"Could not reach threat-designer agent: {exc}") from exc
