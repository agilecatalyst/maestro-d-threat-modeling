"""Optional hardening helpers (v1 local-first)."""

import os
from typing import List, Optional

from fastapi import Header, HTTPException

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")


def parse_cors_origins(raw: Optional[str]) -> List[str]:
    if not raw:
        return ["http://localhost:5173", "http://127.0.0.1:5173"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def require_internal_key(x_internal_key: Optional[str] = Header(default=None, alias="X-Internal-Key")) -> None:
    """When INTERNAL_API_KEY is set, server-to-server calls must present the header."""
    if not INTERNAL_API_KEY:
        return
    if x_internal_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing X-Internal-Key")
