import os
import uuid
from pathlib import Path

STORAGE_PATH = Path(os.getenv("DIAGRAM_STORAGE_PATH", "/data/diagrams"))
STORAGE_PATH.mkdir(parents=True, exist_ok=True)

def save_diagram(file_content: bytes, extension: str) -> str:
    file_uuid = str(uuid.uuid4())
    filename = f"{file_uuid}.{extension}"
    file_path = STORAGE_PATH / filename
    
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    return filename