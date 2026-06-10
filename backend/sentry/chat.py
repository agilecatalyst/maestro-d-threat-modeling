from __future__ import annotations

from typing import Any, Dict, List

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from llm import get_chat_model
from prompt import build_system_prompt
from tools import build_tools

_checkpointer = MemorySaver()


def _extract_reply(messages: List) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            content = message.content
            if isinstance(content, str) and content.strip():
                return content.strip()
            if isinstance(content, list):
                parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        parts.append(block.get("text", ""))
                joined = "\n".join(part for part in parts if part)
                if joined.strip():
                    return joined.strip()
    return "Done."


def _tools_used(messages: List) -> List[str]:
    names: List[str] = []
    for message in messages:
        if isinstance(message, ToolMessage):
            names.append(getattr(message, "name", None) or "tool")
    return names


def run_chat(
    session_id: str,
    threat_model_id: str,
    message: str,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    cache_key = f"{session_id}:{threat_model_id}"
    tools = build_tools(threat_model_id)
    agent = create_react_agent(
        get_chat_model(),
        tools,
        prompt=build_system_prompt(context),
        checkpointer=_checkpointer,
    )
    config = {"configurable": {"thread_id": cache_key}}

    result = agent.invoke({"messages": [HumanMessage(content=message)]}, config=config)
    messages = result.get("messages") or []
    return {
        "type": "message",
        "reply": _extract_reply(messages),
        "tools_used": _tools_used(messages),
    }


def clear_session(session_id: str, threat_model_id: str) -> None:
    # MemorySaver has no public delete; new thread id after clear is enough for v1.
    pass
