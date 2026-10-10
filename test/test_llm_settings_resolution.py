"""Role resolution for tm-agent: DB override, cache, allowlist and fallback."""

import sys
from pathlib import Path

import pytest

AGENT_DIR = Path(__file__).resolve().parent.parent / "backend" / "agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

import llm_settings
from llm_providers import ProviderConfig


@pytest.fixture(autouse=True)
def _clean_cache():
    llm_settings.clear_cache()
    yield
    llm_settings.clear_cache()


def _profile(role):
    return ProviderConfig(
        kind="anthropic",
        model=f"model-for-{role}",
        api_key="k",
        timeout_sec=90.0,
        source="db",
    )


def test_db_profile_overrides_env(monkeypatch):
    monkeypatch.setenv("LOCAL_MODEL", "env-model")
    monkeypatch.setattr(llm_settings, "_db_config", _profile)

    cfg = llm_settings.resolve_config("threats")
    assert cfg.source == "db"
    assert cfg.model == "model-for-threats"
    assert cfg.timeout_sec == 90.0


def test_roles_resolve_independently(monkeypatch):
    monkeypatch.setattr(llm_settings, "_db_config", _profile)
    assert llm_settings.resolve_config("threats").model == "model-for-threats"
    assert llm_settings.resolve_config("sentry").model == "model-for-sentry"


def test_ttl_cache_hits_the_store_once(monkeypatch):
    calls = []

    def counting(role):
        calls.append(role)
        return _profile(role)

    monkeypatch.setattr(llm_settings, "_db_config", counting)
    llm_settings.resolve_config("threats")
    llm_settings.resolve_config("threats")
    assert calls == ["threats"]


def test_store_failure_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("LOCAL_MODEL", "env-model")
    monkeypatch.setenv("INFERENCE_BASE_URL", "http://localhost:1234/v1")

    def boom(role):
        raise RuntimeError("postgres is down")

    monkeypatch.setattr(llm_settings, "_db_config", boom)
    cfg = llm_settings.resolve_config("threats")
    assert cfg.source == "env"
    assert cfg.model == "env-model"


def test_unbound_role_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("LOCAL_MODEL", "env-model")
    monkeypatch.setattr(llm_settings, "_db_config", lambda role: None)
    assert llm_settings.resolve_config("threats").source == "env"


@pytest.mark.parametrize(
    "name,allowed",
    [
        ("INFERENCE_API_KEY", True),
        ("LLM_OPENAI_API_KEY", True),
        ("LLM_ANTHROPIC_API_KEY", True),
        ("POSTGRES_PASSWORD", False),
        ("PATH", False),
        (None, False),
    ],
)
def test_api_key_env_allowlist(monkeypatch, name, allowed):
    if name:
        monkeypatch.setenv(name, "secret-value")
    resolved = llm_settings.lookup_api_key(name)
    assert (resolved == "secret-value") is allowed
