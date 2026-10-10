"""LLM provider profile management, role binding and resolution."""

from __future__ import annotations

import os
import re
import time
from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import LlmProviderProfile, LlmRoleBinding

PROVIDER_KINDS = ("openai_compatible", "openai", "anthropic", "gemini")
PROVIDER_ROLES = ("threats", "sentry")
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


def is_allowed_api_key_env(name: Optional[str]) -> bool:
    return bool(name) and bool(API_KEY_ENV_PATTERN.match(name))


def lookup_api_key(name: Optional[str]) -> Optional[str]:
    """Resolve a secret by env-var name, but only for allowlisted names."""
    if not is_allowed_api_key_env(name):
        return None
    return os.getenv(name) or None


def _validate(payload: dict[str, Any]) -> None:
    kind = payload.get("kind")
    if kind not in PROVIDER_KINDS:
        raise HTTPException(status_code=422, detail=f"Unknown provider kind '{kind}'")
    if kind == "openai_compatible" and not payload.get("base_url"):
        raise HTTPException(
            status_code=422, detail="base_url is required for kind 'openai_compatible'"
        )
    api_key_env = payload.get("api_key_env")
    if api_key_env and not is_allowed_api_key_env(api_key_env):
        raise HTTPException(
            status_code=422,
            detail="api_key_env must be INFERENCE_API_KEY or match LLM_*",
        )


def _iso(value) -> Optional[str]:
    return value.isoformat() if value is not None else None


def serialize_profile(profile: LlmProviderProfile) -> dict[str, Any]:
    return {
        "id": str(profile.id),
        "name": profile.name,
        "kind": profile.kind,
        "base_url": profile.base_url,
        "model": profile.model,
        "api_key_env": profile.api_key_env,
        "key_present": lookup_api_key(profile.api_key_env) is not None,
        "temperature": profile.temperature,
        "max_tokens": profile.max_tokens,
        "timeout_sec": profile.timeout_sec,
        "created_at": _iso(profile.created_at),
        "updated_at": _iso(profile.updated_at),
    }


def list_profiles(db: Session) -> list[dict[str, Any]]:
    rows = db.query(LlmProviderProfile).order_by(LlmProviderProfile.name).all()
    return [serialize_profile(row) for row in rows]


def get_profile(db: Session, profile_id: UUID) -> LlmProviderProfile:
    profile = db.get(LlmProviderProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Provider profile not found")
    return profile


def create_profile(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    _validate(payload)
    profile = LlmProviderProfile(**payload)
    db.add(profile)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Profile name already exists") from exc
    db.refresh(profile)
    return serialize_profile(profile)


def update_profile(db: Session, profile_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
    _validate(payload)
    profile = get_profile(db, profile_id)
    for key, value in payload.items():
        setattr(profile, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Profile name already exists") from exc
    db.refresh(profile)
    return serialize_profile(profile)


def delete_profile(db: Session, profile_id: UUID) -> None:
    profile = get_profile(db, profile_id)
    bound = db.query(LlmRoleBinding).filter(LlmRoleBinding.profile_id == profile.id).first()
    if bound is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Profile is bound to role '{bound.role}'; rebind that role first",
        )
    db.delete(profile)
    db.commit()


def get_role_bindings(db: Session) -> dict[str, Optional[dict[str, Any]]]:
    bindings = {role: None for role in PROVIDER_ROLES}
    for binding in db.query(LlmRoleBinding).all():
        profile = db.get(LlmProviderProfile, binding.profile_id)
        if profile is not None:
            bindings[binding.role] = serialize_profile(profile)
    return bindings


def set_role_binding(db: Session, role: str, profile_id: UUID) -> dict[str, Any]:
    if role not in PROVIDER_ROLES:
        raise HTTPException(status_code=422, detail=f"Unknown role '{role}'")
    profile = get_profile(db, profile_id)
    binding = db.get(LlmRoleBinding, role)
    if binding is None:
        db.add(LlmRoleBinding(role=role, profile_id=profile.id))
    else:
        binding.profile_id = profile.id
    db.commit()
    return serialize_profile(profile)


def _env_kind() -> str:
    raw = (os.getenv("MODEL_PROVIDER") or "").strip().lower()
    return _KIND_ALIASES.get(raw, "openai_compatible")


def _env_resolved(role: str) -> dict[str, Any]:
    try:
        timeout = float(os.getenv("INFERENCE_REQUEST_TIMEOUT_SEC", "180"))
    except ValueError:
        timeout = 180.0
    return {
        "role": role,
        "kind": _env_kind(),
        "model": os.getenv("LOCAL_MODEL") or "",
        "base_url": os.getenv("INFERENCE_BASE_URL"),
        "api_key_env": "INFERENCE_API_KEY",
        "key_present": bool(os.getenv("INFERENCE_API_KEY")),
        "temperature": None,
        "max_tokens": None,
        "timeout_sec": timeout,
        "source": "env",
    }


def resolve(db: Session, role: str) -> dict[str, Any]:
    """Effective provider config for a role; falls back to env when unbound."""
    if role not in PROVIDER_ROLES:
        raise HTTPException(status_code=422, detail=f"Unknown role '{role}'")
    binding = db.get(LlmRoleBinding, role)
    if binding is None:
        return _env_resolved(role)
    profile = db.get(LlmProviderProfile, binding.profile_id)
    if profile is None:
        return _env_resolved(role)
    return {
        "role": role,
        "kind": profile.kind,
        "model": profile.model,
        "base_url": profile.base_url,
        "api_key_env": profile.api_key_env,
        "key_present": lookup_api_key(profile.api_key_env) is not None,
        "temperature": profile.temperature,
        "max_tokens": profile.max_tokens,
        "timeout_sec": float(profile.timeout_sec or 180),
        "source": "db",
    }


def test_profile(db: Session, profile_id: UUID) -> dict[str, Any]:
    """Minimal live round trip against the profile's provider."""
    import httpx

    profile = get_profile(db, profile_id)
    api_key = lookup_api_key(profile.api_key_env)
    started = time.perf_counter()

    def elapsed() -> int:
        return int((time.perf_counter() - started) * 1000)

    try:
        if profile.kind in ("openai_compatible", "openai"):
            base_url = (profile.base_url or "https://api.openai.com/v1").rstrip("/")
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{base_url}/models", headers=headers)
                response.raise_for_status()
                data = response.json()
            models = data if isinstance(data, list) else data.get("data", [])
            ids = [str(item.get("id", "")) for item in models if isinstance(item, dict)]
            found = profile.model in ids
            return {
                "ok": True,
                "latency_ms": elapsed(),
                "detail": f"{len(ids)} model(s) available; '{profile.model}' "
                + ("found" if found else "not listed"),
            }

        if profile.kind == "anthropic":
            if not api_key:
                return {"ok": False, "latency_ms": elapsed(), "error": "No API key resolved from api_key_env"}
            base_url = (profile.base_url or "https://api.anthropic.com").rstrip("/")
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{base_url}/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": profile.model,
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "ping"}],
                    },
                )
                response.raise_for_status()
            return {"ok": True, "latency_ms": elapsed(), "detail": f"'{profile.model}' responded"}

        if profile.kind == "gemini":
            if not api_key:
                return {"ok": False, "latency_ms": elapsed(), "error": "No API key resolved from api_key_env"}
            base_url = (profile.base_url or "https://generativelanguage.googleapis.com").rstrip("/")
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{base_url}/v1beta/models/{profile.model}",
                    headers={"x-goog-api-key": api_key},
                )
                response.raise_for_status()
            return {"ok": True, "latency_ms": elapsed(), "detail": f"'{profile.model}' is available"}

        return {"ok": False, "latency_ms": elapsed(), "error": f"Unknown provider kind '{profile.kind}'"}
    except Exception as exc:  # noqa: BLE001 - surfaced to the operator as text
        return {"ok": False, "latency_ms": elapsed(), "error": str(exc)}
