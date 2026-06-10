"""Build AssetsList from JSON or plain-text LLM output."""

from __future__ import annotations

from typing import List, Optional

from pydantic import ValidationError

from asset_text_blocks import extract_asset_dicts_from_text
from assets_schema import Assets, AssetsList
from structured_tool_json import tool_arguments_if_name, try_parse_json_object


def parse_assets_list_from_text(text: str) -> Optional[AssetsList]:
    parsed = try_parse_json_object(text)
    if parsed:
        args = tool_arguments_if_name(parsed, "AssetsList")
        if args is not None:
            try:
                return AssetsList.model_validate(args)
            except ValidationError:
                pass
        if "assets" in parsed and isinstance(parsed.get("assets"), list):
            try:
                return AssetsList.model_validate(parsed)
            except ValidationError:
                pass

    raw_rows = extract_asset_dicts_from_text(text)
    if not raw_rows:
        return None

    assets: List[Assets] = []
    for row in raw_rows:
        try:
            assets.append(Assets(**row))
        except ValidationError:
            continue

    if not assets:
        return None
    return AssetsList(assets=assets)
