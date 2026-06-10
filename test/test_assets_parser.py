import sys
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent.parent / "backend" / "agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from asset_text_blocks import extract_asset_dicts_from_text
from asset_text_parser import parse_assets_list_from_text

SAMPLE_BLOCKS = """
Type: Asset

Name: Database

Description: Central data store for application data.

Criticality: High


Type: Entity

Name: External API

Description: Third-party integration at trust boundary.

Criticality: Medium
"""

SAMPLE_JSON = """
{"name": "AssetsList", "arguments": {"assets": [
  {"type": "Asset", "name": "Web Server", "description": "Hosts the UI", "criticality": "High"}
]}}
"""


def test_extract_two_blocks():
    rows = extract_asset_dicts_from_text(SAMPLE_BLOCKS)
    assert rows is not None
    assert len(rows) == 2
    assert rows[0]["name"] == "Database"
    assert rows[1]["type"] == "Entity"


def test_parse_json_wrapper():
    result = parse_assets_list_from_text(SAMPLE_JSON)
    assert result is not None
    assert len(result.assets) == 1
    assert result.assets[0].name == "Web Server"


def test_parse_plain_blocks_to_assets_list():
    result = parse_assets_list_from_text(SAMPLE_BLOCKS)
    assert result is not None
    assert len(result.assets) == 2
    assert result.assets[0].criticality == "High"
