"""Build FlowsList from JSON or plain-text LLM output."""

# Portions adapted from awslabs/threat-designer (Apache-2.0)
# https://github.com/awslabs/threat-designer

from __future__ import annotations

from typing import List, Optional

from pydantic import ValidationError

from flows_schema import DataFlow, FlowsList, ThreatSource, TrustBoundary
from flows_text_blocks import extract_flows_dict_from_text
from structured_tool_json import tool_arguments_if_name, try_parse_json_object


def parse_flows_list_from_text(text: str) -> Optional[FlowsList]:
    parsed = try_parse_json_object(text)
    if parsed:
        args = tool_arguments_if_name(parsed, "FlowsList")
        if args is not None:
            try:
                return FlowsList.model_validate(args)
            except ValidationError:
                pass
        if all(key in parsed for key in ("data_flows", "trust_boundaries", "threat_sources")):
            try:
                return FlowsList.model_validate(parsed)
            except ValidationError:
                pass

    raw = extract_flows_dict_from_text(text)
    if not raw:
        return None

    try:
        return FlowsList(
            data_flows=[DataFlow(**row) for row in raw["data_flows"]],
            trust_boundaries=[TrustBoundary(**row) for row in raw["trust_boundaries"]],
            threat_sources=[ThreatSource(**row) for row in raw["threat_sources"]],
        )
    except ValidationError:
        return None
