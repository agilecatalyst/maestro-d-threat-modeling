"""Provider registry unit tests (no live LLM, no provider SDKs required)."""

import sys
import types
from pathlib import Path

import pytest

AGENT_DIR = Path(__file__).resolve().parent.parent / "backend" / "agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

import llm_settings
from llm_providers import PROVIDER_KINDS, ProviderConfig, build_chat_model


class _FakeModel:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


def _install_fake(monkeypatch, module_name, attr):
    module = types.ModuleType(module_name)
    setattr(module, attr, _FakeModel)
    monkeypatch.setitem(sys.modules, module_name, module)
    return module


def test_openai_compatible_wires_base_url(monkeypatch):
    _install_fake(monkeypatch, "langchain_openai", "ChatOpenAI")
    cfg = ProviderConfig(
        kind="openai_compatible",
        model="qwen3",
        base_url="http://host.docker.internal:1234/v1",
        api_key="secret",
        timeout_sec=42.0,
    )
    model = build_chat_model(cfg)
    assert model.kwargs["base_url"] == "http://host.docker.internal:1234/v1"
    assert model.kwargs["model"] == "qwen3"
    assert model.kwargs["api_key"] == "secret"
    assert model.kwargs["request_timeout"] == 42.0


def test_openai_cloud_has_no_base_url(monkeypatch):
    _install_fake(monkeypatch, "langchain_openai", "ChatOpenAI")
    model = build_chat_model(
        ProviderConfig(kind="openai", model="gpt-4o-mini", api_key="sk-x")
    )
    assert "base_url" not in model.kwargs
    assert model.kwargs["model"] == "gpt-4o-mini"


def test_anthropic_factory(monkeypatch):
    _install_fake(monkeypatch, "langchain_anthropic", "ChatAnthropic")
    model = build_chat_model(
        ProviderConfig(
            kind="anthropic",
            model="claude-sonnet-4",
            api_key="k",
            temperature=0.2,
            max_tokens=1024,
        )
    )
    assert model.kwargs["model"] == "claude-sonnet-4"
    assert model.kwargs["temperature"] == 0.2
    assert model.kwargs["max_tokens"] == 1024


def test_gemini_factory(monkeypatch):
    _install_fake(monkeypatch, "langchain_google_genai", "ChatGoogleGenerativeAI")
    model = build_chat_model(
        ProviderConfig(kind="gemini", model="gemini-2.5-pro", api_key="k", max_tokens=8)
    )
    assert model.kwargs["google_api_key"] == "k"
    assert model.kwargs["max_output_tokens"] == 8


def test_all_kinds_are_registered():
    for kind in PROVIDER_KINDS:
        assert kind in ("openai_compatible", "openai", "anthropic", "gemini")


def test_unknown_kind_raises():
    with pytest.raises(ValueError, match="unknown provider kind"):
        build_chat_model(ProviderConfig(kind="bedrock", model="x"))


def test_openai_compatible_requires_base_url():
    with pytest.raises(ValueError, match="base_url"):
        build_chat_model(ProviderConfig(kind="openai_compatible", model="x"))


def test_missing_sdk_names_the_package(monkeypatch):
    monkeypatch.setitem(sys.modules, "langchain_anthropic", None)
    with pytest.raises(RuntimeError, match="langchain-anthropic"):
        build_chat_model(ProviderConfig(kind="anthropic", model="x", api_key="k"))


def test_legacy_env_path_unchanged(monkeypatch):
    monkeypatch.setenv("INFERENCE_BASE_URL", "http://localhost:1234/v1")
    monkeypatch.setenv("LOCAL_MODEL", "legacy-model")
    monkeypatch.setenv("INFERENCE_API_KEY", "lm-studio")
    monkeypatch.setenv("INFERENCE_REQUEST_TIMEOUT_SEC", "180")
    monkeypatch.delenv("MODEL_PROVIDER", raising=False)
    monkeypatch.setattr(llm_settings, "_db_config", lambda role: None)
    llm_settings.clear_cache()

    cfg = llm_settings.resolve_config("threats")
    assert cfg.kind == "openai_compatible"
    assert cfg.base_url == "http://localhost:1234/v1"
    assert cfg.model == "legacy-model"
    assert cfg.api_key == "lm-studio"
    assert cfg.timeout_sec == 180.0
    assert cfg.source == "env"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("ollama", "openai_compatible"),
        ("lmstudio", "openai_compatible"),
        ("openai", "openai"),
        ("claude", "anthropic"),
        ("gemini", "gemini"),
        ("nonsense", "openai_compatible"),
    ],
)
def test_model_provider_env_maps_to_kind(monkeypatch, raw, expected):
    monkeypatch.setenv("MODEL_PROVIDER", raw)
    monkeypatch.setattr(llm_settings, "_db_config", lambda role: None)
    llm_settings.clear_cache()
    assert llm_settings.resolve_config().kind == expected
