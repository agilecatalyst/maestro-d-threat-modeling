"""Resolve the effective provider config for a role.

Sentry has no database credentials, so it asks the api service for the
resolved config and looks the secret up locally from an allowlisted
environment variable. Any transport failure falls back to the legacy
environment configuration so chat keeps working.
"""

import logging
import os
import re
import time
from typing import Dict, Optional, Tuple

from dotenv import load_dotenv

from llm_providers import PROVIDER_KINDS, ProviderConfig

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_ROLE = "sentry"
CACHE_TTL_SEC = 30.0
RESOLVE_TIMEOUT_SEC = 5.0
API_KEY_ENV_PATTERN = re.compile(r"^(INFERENCE_API_KEY|LLM_[A-Z0-9_]+)$")

_KIND_ALIASES = {
    "": "openai_compatible",
    "ollama": "openai_compatible",
    "lmstudio": "openai_compatible",
    "lm_studio": "openai_compatible",
    "omlx": "openai_compatible",
    "local": "openai_compatible",
    "openai_compatible": "openai_compatible",
    "openai": "openai",
    "anthropic": "anthropic",
    "claude": "anthropic",
    "gemini": "gemini",
    "google": "gemini",
}

_cache: Dict[str, Tuple[float, ProviderConfig]] = {}


def lookup_api_key(name: Optional[str]) -> Optional[str]:
    if not name or not API_KEY_ENV_PATTERN.match(name):
        return None
    return os.getenv(name) or None


def _env_kind() -> str:
    raw = (os.getenv("MODEL_PROVIDER") or "").strip().lower()
    kind = _KIND_ALIASES.get(raw, "openai_compatible")
    return kind if kind in PROVIDER_KINDS else "openai_compatible"


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def env_config() -> ProviderConfig:
    return ProviderConfig(
        kind=_env_kind(),
        model=os.getenv("LOCAL_MODEL") or "",
        base_url=os.getenv("INFERENCE_BASE_URL"),
        api_key=os.getenv("INFERENCE_API_KEY"),
        timeout_sec=_env_float("INFERENCE_REQUEST_TIMEOUT_SEC", 180.0),
        source="env",
    )


def _api_config(role: str) -> Optional[ProviderConfig]:
    import httpx

    base = os.getenv("THREAT_API_URL", "http://api:8000").rstrip("/")
    headers = {}
    internal_key = os.getenv("INTERNAL_API_KEY", "")
    if internal_key:
        headers["X-Internal-Key"] = internal_key

    with httpx.Client(timeout=RESOLVE_TIMEOUT_SEC) as client:
        response = client.get(f"{base}/admin/llm-providers/resolved/{role}", headers=headers)
        response.raise_for_status()
        data = response.json()

    if data.get("source") != "db":
        return None
    return ProviderConfig(
        kind=data["kind"],
        model=data.get("model") or "",
        base_url=data.get("base_url"),
        api_key=lookup_api_key(data.get("api_key_env")),
        temperature=data.get("temperature"),
        max_tokens=data.get("max_tokens"),
        timeout_sec=float(data.get("timeout_sec") or 180),
        source="db",
    )


def clear_cache() -> None:
    _cache.clear()


def resolve_config(role: str = DEFAULT_ROLE) -> ProviderConfig:
    cached = _cache.get(role)
    now = time.monotonic()
    if cached is not None and now - cached[0] < CACHE_TTL_SEC:
        return cached[1]

    try:
        config = _api_config(role)
    except Exception as exc:  # noqa: BLE001 - chat must survive an unreachable api
        logger.warning("LLM settings lookup failed for role '%s': %s", role, exc)
        config = None

    if config is None:
        config = env_config()

    _cache[role] = (now, config)
    return config
