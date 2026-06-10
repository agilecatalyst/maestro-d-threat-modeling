"""In-memory rate limiting for Sentry chat invocations."""

import os
import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request

LIMIT = 10
WINDOW = 60

_buckets: dict[str, list[float]] = defaultdict(list)
_lock = Lock()


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def check_sentry_rate_limit(request: Request) -> None:
    if os.getenv("API_RATE_LIMIT_ENABLED", "true").lower() in ("0", "false", "no"):
        return
    key = client_ip(request)
    now = time.time()
    with _lock:
        recent = [t for t in _buckets[key] if now - t < WINDOW]
        if len(recent) >= LIMIT:
            retry_after = max(1, int(WINDOW - (now - recent[0])))
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(retry_after)},
            )
        recent.append(now)
        _buckets[key] = recent
