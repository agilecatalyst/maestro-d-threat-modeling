"""Provider registry: builds a chat model from a provider-agnostic config."""

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable, Dict, Optional

PROVIDER_KINDS = ("openai_compatible", "openai", "anthropic", "gemini")


@dataclass(frozen=True)
class ProviderConfig:
    kind: str
    model: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout_sec: float = 180.0
    source: str = "env"


def _load(module_name: str, attr: str, package: str, kind: str) -> Any:
    try:
        module = import_module(module_name)
    except ImportError as exc:
        raise RuntimeError(
            f"provider '{kind}' requires the '{package}' package to be installed"
        ) from exc
    return getattr(module, attr)


def _openai_compatible(cfg: ProviderConfig) -> Any:
    if not cfg.base_url:
        raise ValueError("provider 'openai_compatible' requires a base_url")
    chat_openai = _load("langchain_openai", "ChatOpenAI", "langchain-openai", cfg.kind)
    kwargs: Dict[str, Any] = {
        "base_url": cfg.base_url,
        "api_key": cfg.api_key or "not-needed",
        "model": cfg.model,
        "request_timeout": cfg.timeout_sec,
    }
    if cfg.temperature is not None:
        kwargs["temperature"] = cfg.temperature
    if cfg.max_tokens is not None:
        kwargs["max_tokens"] = cfg.max_tokens
    return chat_openai(**kwargs)


def _openai(cfg: ProviderConfig) -> Any:
    chat_openai = _load("langchain_openai", "ChatOpenAI", "langchain-openai", cfg.kind)
    kwargs: Dict[str, Any] = {
        "api_key": cfg.api_key,
        "model": cfg.model,
        "request_timeout": cfg.timeout_sec,
    }
    if cfg.temperature is not None:
        kwargs["temperature"] = cfg.temperature
    if cfg.max_tokens is not None:
        kwargs["max_tokens"] = cfg.max_tokens
    return chat_openai(**kwargs)


def _anthropic(cfg: ProviderConfig) -> Any:
    chat_anthropic = _load(
        "langchain_anthropic", "ChatAnthropic", "langchain-anthropic", cfg.kind
    )
    kwargs: Dict[str, Any] = {
        "api_key": cfg.api_key,
        "model": cfg.model,
        "timeout": cfg.timeout_sec,
    }
    if cfg.temperature is not None:
        kwargs["temperature"] = cfg.temperature
    if cfg.max_tokens is not None:
        kwargs["max_tokens"] = cfg.max_tokens
    if cfg.base_url:
        kwargs["base_url"] = cfg.base_url
    return chat_anthropic(**kwargs)


def _gemini(cfg: ProviderConfig) -> Any:
    chat_gemini = _load(
        "langchain_google_genai",
        "ChatGoogleGenerativeAI",
        "langchain-google-genai",
        cfg.kind,
    )
    kwargs: Dict[str, Any] = {
        "google_api_key": cfg.api_key,
        "model": cfg.model,
        "timeout": cfg.timeout_sec,
    }
    if cfg.temperature is not None:
        kwargs["temperature"] = cfg.temperature
    if cfg.max_tokens is not None:
        kwargs["max_output_tokens"] = cfg.max_tokens
    return chat_gemini(**kwargs)


_REGISTRY: Dict[str, Callable[[ProviderConfig], Any]] = {
    "openai_compatible": _openai_compatible,
    "openai": _openai,
    "anthropic": _anthropic,
    "gemini": _gemini,
}


def build_chat_model(cfg: ProviderConfig) -> Any:
    factory = _REGISTRY.get(cfg.kind)
    if factory is None:
        raise ValueError(
            f"unknown provider kind '{cfg.kind}'; expected one of {', '.join(PROVIDER_KINDS)}"
        )
    return factory(cfg)
