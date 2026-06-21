import os
import uuid
from pathlib import Path

STORAGE_PATH = Path(os.getenv("DIAGRAM_STORAGE_PATH", "/data/diagrams"))
STORAGE_PATH.mkdir(parents=True, exist_ok=True)


def _safe_path(relative_path: str) -> Path:
    candidate = (STORAGE_PATH / relative_path).resolve()
    if not str(candidate).startswith(str(STORAGE_PATH.resolve())):
        raise ValueError("Invalid diagram path")
    return candidate


def save_diagram(file_content: bytes, extension: str) -> str:
    file_uuid = str(uuid.uuid4())
    filename = f"{file_uuid}.{extension}"
    file_path = STORAGE_PATH / filename

    with open(file_path, "wb") as f:
        f.write(file_content)

    return filename


def resolve_diagram_path(relative_path: str) -> Path:
    return _safe_path(relative_path)


def assert_safe_diagram_relative_path(relative_path: str) -> None:
    """Reject path traversal; does not require the file to exist."""
    _safe_path(relative_path)


def delete_diagram(relative_path: str | None) -> None:
    if not relative_path:
        return
    try:
        path = _safe_path(relative_path)
    except ValueError:
        return
    if path.is_file():
        path.unlink()