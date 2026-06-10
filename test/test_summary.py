import json
import time
from pathlib import Path
from typing import Optional, Tuple

import pytest
import requests

API_URL = "http://localhost:8000"
AGENT_URL = "http://localhost:8080"
SAMPLE_PNG = Path(__file__).resolve().parent / "fixtures" / "sample.png"
DESCRIPTION = "Three-tier web app: browser, API, PostgreSQL database."
POLL_TIMEOUT_SEC = 180


def _stack_up() -> bool:
    try:
        requests.get(f"{API_URL}/health", timeout=5).raise_for_status()
        requests.get(f"{AGENT_URL}/ping", timeout=5).raise_for_status()
        return True
    except requests.RequestException:
        return False


def _job_status(job_id: str) -> Tuple[Optional[str], Optional[str]]:
    result = requests.get(f"{API_URL}/threat-designer/status/{job_id}", timeout=10)
    if result.status_code != 200:
        return None, None
    body = result.json()
    detail = body.get("detail")
    detail_raw = json.dumps(detail) if isinstance(detail, dict) else None
    return body.get("state"), detail_raw


@pytest.fixture(scope="module", autouse=True)
def require_compose_stack():
    if not _stack_up():
        pytest.skip("api/agent not reachable — run docker compose up -d")


def test_upload_start_job_complete_via_api():
    with SAMPLE_PNG.open("rb") as handle:
        upload = requests.post(
            f"{API_URL}/threat-designer/diagrams/",
            files={"file": ("sample.png", handle, "image/png")},
            timeout=15,
        )
    assert upload.status_code == 200
    created = upload.json()

    start = requests.post(
        f"{API_URL}/threat-designer",
        json={
            "id": created["id"],
            "description": DESCRIPTION,
            "application_type": "hybrid",
        },
        timeout=15,
    )
    assert start.status_code == 200
    assert start.json()["id"] == created["id"]

    deadline = time.time() + POLL_TIMEOUT_SEC
    state = None
    detail_raw = None
    while time.time() < deadline:
        state, detail_raw = _job_status(created["id"])
        if state in ("COMPLETE", "FAILED"):
            break
        time.sleep(3)

    assert state == "COMPLETE", f"got state={state!r} detail={detail_raw!r}"
    detail = json.loads(detail_raw)
    assert len(detail.get("summary", "")) > 20
    assert isinstance(detail.get("assets"), list)
    assert len(detail["assets"]) >= 1
    flows = detail.get("flows", {})
    assert isinstance(flows.get("data_flows"), list)
    assert len(flows["data_flows"]) >= 1
    threats = detail.get("threats", [])
    assert isinstance(threats, list)
    assert len(threats) >= 3
    assert detail.get("meta", {}).get("threat_count", len(threats)) >= 3
