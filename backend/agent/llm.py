from llm_providers import build_chat_model
from llm_settings import DEFAULT_ROLE, resolve_config


def get_chat_model(role: str = DEFAULT_ROLE):
    return build_chat_model(resolve_config(role))
