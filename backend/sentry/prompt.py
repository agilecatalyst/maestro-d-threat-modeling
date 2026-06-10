import json
from typing import Any, Dict, List


def build_system_prompt(context: Dict[str, Any]) -> str:
    summary = context.get("summary") or "No summary."
    assets = context.get("assets") or []
    flows = context.get("flows") or {}
    threats = context.get("threats") or []
    title = context.get("title") or "Threat model"

    asset_lines = "\n".join(
        f"- {row.get('name', '?')} ({row.get('criticality', 'Medium')})"
        for row in assets
    )
    flow_lines = "\n".join(
        f"- {row.get('source_entity', '?')} → {row.get('target_entity', '?')}: "
        f"{row.get('flow_description', '?')}"
        for row in (flows.get("data_flows") or [])[:8]
    )
    threat_lines = "\n".join(
        f"- [{row.get('stride_category', '?')}] {row.get('name', '?')}: {row.get('description', '')[:120]}"
        for row in threats[:20]
    )

    return (
        "You are Sentry, a security architect assistant for threat modeling.\n"
        "You help analyze STRIDE threats, find gaps, and improve mitigations.\n"
        "Use tools to add, edit, or delete threats when the user asks for catalog changes.\n"
        "Be concise and practical. Do not invent architecture facts not present in context.\n\n"
        f"Threat model: {title}\n\n"
        f"Summary:\n{summary}\n\n"
        f"Assets:\n{asset_lines or '- none listed'}\n\n"
        f"Data flows:\n{flow_lines or '- none listed'}\n\n"
        f"Current threats ({len(threats)}):\n{threat_lines or '- none yet'}\n"
    )


def context_from_input(input_data: Dict[str, Any]) -> Dict[str, Any]:
    context = input_data.get("context") or {}
    if isinstance(context, str):
        try:
            context = json.loads(context)
        except json.JSONDecodeError:
            context = {}
    threat_model = context.get("threatModel") or context.get("threat_model") or context
    if not isinstance(threat_model, dict):
        return {}
    return {
        "title": threat_model.get("title"),
        "summary": threat_model.get("summary"),
        "assets": threat_model.get("assets") or [],
        "flows": threat_model.get("flows") or {},
        "threats": threat_model.get("threats") or [],
    }
