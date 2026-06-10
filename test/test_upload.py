import uuid
from pathlib import Path

import requests

BASE_URL = "http://localhost:8000/threat-designer/diagrams"
SAMPLE_PNG = Path(__file__).resolve().parent / "fixtures" / "sample.png"


def test_upload_and_get_roundtrip():
    with SAMPLE_PNG.open("rb") as handle:
        post_resp = requests.post(
            f"{BASE_URL}/",
            files={"file": ("sample.png", handle, "image/png")},
            timeout=10,
        )
    assert post_resp.status_code == 200
    created = post_resp.json()

    get_resp = requests.get(f"{BASE_URL}/{created['id']}", timeout=10)
    assert get_resp.status_code == 200
    meta = get_resp.json()
    assert meta["id"] == created["id"]
    assert meta["owner"] == created["owner"]
    assert meta["diagram_path"] == created["diagram_path"]
    assert meta["state"] == "PENDING"
    assert "title" in meta


def test_get_unknown_returns_404():
    resp = requests.get(f"{BASE_URL}/{uuid.uuid4()}", timeout=10)
    assert resp.status_code == 404
