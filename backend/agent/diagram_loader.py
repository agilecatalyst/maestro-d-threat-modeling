import os
import base64
from pathlib import Path
from typing import Optional

STORAGE_PATH = Path(os.getenv("DIAGRAM_STORAGE_PATH", "/data/diagrams"))

def load_diagram_data_url(relative_path: str) -> Optional[str]:
    file_path = STORAGE_PATH / relative_path
    if not file_path.exists():
        return None
    
    with open(file_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    
    extension = file_path.suffix.lower().replace(".", "")
    return f"data:image/{extension};base64,{encoded}"