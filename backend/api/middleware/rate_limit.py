"""In-memory per-IP rate limiting (v1 — no Redis)."""

import os
import time
from collections import defaultdict
from threading import Lock
from typing import Callable

from fastapi import HTTPException, Request


def _rate_limits_enabled() -> bool:
    return os.getenv("API_RATE_LIMIT_ENABLED", "true").lower() not in ("0", "false", "no")

LIMITS: dict[str, tuple[int, int]] = {
    "upload": (10, 60),
    "start_job": (5, 60),
    "scan_flow": (3, 60),
    "sentry_chat": (10, 60),
}

_buckets: dict[tuple[str, str], list[float]] = defaultdict(list)
_lock = Lock()


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def check_rate_limit(request: Request, bucket: str) -> None:
    if not _rate_limits_enabled():
        return
    if bucket not in LIMITS:
        return
    limit, window = LIMITS[bucket]
    key = (bucket, client_ip(request))
    now = time.time()
    with _lock:
        recent = [t for t in _buckets[key] if now - t < window]
        if len(recent) >= limit:
            retry_after = max(1, int(window - (now - recent[0])))
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(retry_after)},
            )
        recent.append(now)
        _buckets[key] = recent


def rate_limit_dependency(bucket: str) -> Callable:
    def _dependency(request: Request) -> None:
        check_rate_limit(request, bucket)

    return _dependency


def reset_buckets_for_tests() -> None:
    with _lock:
        _buckets.clear()
