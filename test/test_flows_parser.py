import sys
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent.parent / "backend" / "agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from flows_text_blocks import extract_flows_dict_from_text
from flows_text_parser import parse_flows_list_from_text

SAMPLE = """
<data_flow>
flow_description: Web Application queries Database
source_entity: Web Application
target_entity: Database
</data_flow>
<trust_boundary>
purpose: Network boundary between users and app
source_entity: Browser
target_entity: Web Application
</trust_boundary>
## Threat Actors
| Category | Description | Examples |
|----------|-------------|----------|
| External Threat Actors | Attackers on public endpoints | Web attacker |
"""


def test_extract_flow_blocks():
    data = extract_flows_dict_from_text(SAMPLE)
    assert data is not None
    assert len(data["data_flows"]) == 1
    assert len(data["trust_boundaries"]) == 1
    assert len(data["threat_sources"]) == 1


def test_parse_flows_list():
    result = parse_flows_list_from_text(SAMPLE)
    assert result is not None
    assert result.data_flows[0].target_entity == "Database"
    assert result.threat_sources[0].category == "External Threat Actors"
