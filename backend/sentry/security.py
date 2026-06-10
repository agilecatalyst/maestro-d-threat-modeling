import os
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()


def parse_cors_origins(raw: Optional[str]) -> List[str]:
    if not raw:
        return ["http://localhost:5173", "http://127.0.0.1:5173"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]
