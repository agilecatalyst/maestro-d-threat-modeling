from typing import Any, Dict

import httpx

from llm_settings import resolve_config

SERVICE = "maestro-d-agent"
CLOUD_DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com",
    "gemini": "https://generativelanguage.googleapis.com",
}


def _base_payload(cfg) -> Dict[str, Any]:
    return {
        "service": SERVICE,
        "provider_kind": cfg.kind,
        "config_source": cfg.source,
        "inference_base_url": cfg.base_url,
        "local_model": cfg.model,
    }


def _probe_openai_compatible(cfg) -> Dict[str, Any]:
    base_url = (cfg.base_url or CLOUD_DEFAULT_BASE_URLS.get(cfg.kind, "")).rstrip("/")
    if not base_url:
        return {
            "status": "disconnected",
            **_base_payload(cfg),
            "models_count": 0,
            "model_loaded": False,
            "error": "INFERENCE_BASE_URL not set",
        }

    headers = {"Authorization": f"Bearer {cfg.api_key}"} if cfg.api_key else {}
    with httpx.Client(timeout=5.0) as client:
        response = client.get(f"{base_url}/models", headers=headers)
        response.raise_for_status()
        data = response.json()

    models_list = data if isinstance(data, list) else data.get("data", [])
    model_loaded = bool(cfg.model) and any(
        cfg.model in str(m.get("id", "")) for m in models_list if isinstance(m, dict)
    )
    return {
        "status": "connected",
        **_base_payload(cfg),
        "models_count": len(models_list),
        "model_loaded": model_loaded,
    }


def _probe_anthropic(cfg) -> Dict[str, Any]:
    base_url = (cfg.base_url or CLOUD_DEFAULT_BASE_URLS["anthropic"]).rstrip("/")
    if not cfg.api_key:
        raise RuntimeError("No API key resolved for the anthropic provider")
    with httpx.Client(timeout=5.0) as client:
        response = client.get(
            f"{base_url}/v1/models",
            headers={"x-api-key": cfg.api_key, "anthropic-version": "2023-06-01"},
        )
        response.raise_for_status()
        data = response.json()
    models_list = data.get("data", []) if isinstance(data, dict) else []
    return {
        "status": "connected",
        **_base_payload(cfg),
        "models_count": len(models_list),
        "model_loaded": any(cfg.model == str(m.get("id", "")) for m in models_list),
    }


def _probe_gemini(cfg) -> Dict[str, Any]:
    base_url = (cfg.base_url or CLOUD_DEFAULT_BASE_URLS["gemini"]).rstrip("/")
    if not cfg.api_key:
        raise RuntimeError("No API key resolved for the gemini provider")
    with httpx.Client(timeout=5.0) as client:
        response = client.get(
            f"{base_url}/v1beta/models", headers={"x-goog-api-key": cfg.api_key}
        )
        response.raise_for_status()
        data = response.json()
    models_list = data.get("models", []) if isinstance(data, dict) else []
    return {
        "status": "connected",
        **_base_payload(cfg),
        "models_count": len(models_list),
        "model_loaded": any(cfg.model in str(m.get("name", "")) for m in models_list),
    }


def check_inference() -> Dict[str, Any]:
    cfg = resolve_config("threats")
    try:
        if cfg.kind in ("openai_compatible", "openai"):
            return _probe_openai_compatible(cfg)
        if cfg.kind == "anthropic":
            return _probe_anthropic(cfg)
        if cfg.kind == "gemini":
            return _probe_gemini(cfg)
        raise RuntimeError(f"Unknown provider kind '{cfg.kind}'")
    except Exception as e:
        return {
            "status": "disconnected",
            **_base_payload(cfg),
            "models_count": 0,
            "model_loaded": False,
            "error": str(e),
        }
