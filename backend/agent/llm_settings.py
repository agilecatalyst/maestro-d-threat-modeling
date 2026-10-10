"""Resolve the effective provider config for a role.

Lookup order: the ``llm_role_bindings`` / ``llm_provider_profiles`` tables
owned by the api service, then the legacy environment variables. Results are
cached in-process for a short TTL so a pipeline run does not hit Postgres for
every node. Secrets are never stored: a profile only references an allowlisted
environment variable name.
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

DEFAULT_ROLE = "threats"
CACHE_TTL_SEC = 30.0
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


def _db_config(role: str) -> Optional[ProviderConfig]:
    from sqlalchemy import text

    from db import SessionLocal

    db = SessionLocal()
    try:
        row = db.execute(
            text(
                "SELECT p.kind, p.base_url, p.model, p.api_key_env, p.temperature, "
                "p.max_tokens, p.timeout_sec "
                "FROM llm_role_bindings b "
                "JOIN llm_provider_profiles p ON p.id = b.profile_id "
                "WHERE b.role = :role"
            ),
            {"role": role},
        ).fetchone()
    finally:
        db.close()

    if row is None:
        return None
    return ProviderConfig(
        kind=row[0],
        base_url=row[1],
        model=row[2],
        api_key=lookup_api_key(row[3]),
        temperature=row[4],
        max_tokens=row[5],
        timeout_sec=float(row[6] or 180),
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
        config = _db_config(role)
    except Exception as exc:  # noqa: BLE001 - never break the pipeline on settings lookup
        logger.warning("LLM settings lookup failed for role '%s': %s", role, exc)
        config = None

    if config is None:
        config = env_config()

    _cache[role] = (now, config)
    return config
