import base64
import os
from pathlib import Path
from typing import Optional

STORAGE_PATH = Path(os.getenv("DIAGRAM_STORAGE_PATH", "/data/diagrams"))


def _safe_path(relative_path: str) -> Path:
    candidate = (STORAGE_PATH / relative_path).resolve()
    if not str(candidate).startswith(str(STORAGE_PATH.resolve())):
        raise ValueError("Invalid diagram path")
    return candidate


def load_diagram_data_url(relative_path: str) -> Optional[str]:
    try:
        file_path = _safe_path(relative_path)
    except ValueError:
        return None
    if not file_path.exists():
        return None

    with open(file_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    extension = file_path.suffix.lower().replace(".", "")
    return f"data:image/{extension};base64,{encoded}"
