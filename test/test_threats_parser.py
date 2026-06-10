import sys
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent.parent / "backend" / "agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from threat_catalog import ThreatCatalog
from threat_tools import gap_analysis
from threats_schema import Threat, ThreatsList
from threats_text_parser import parse_threats_list_from_text

SAMPLE_JSON = """
{"name": "add_threats", "arguments": {"threats": {"threats": [
  {
    "name": "SQL Injection via Web Application",
    "stride_category": "Tampering",
    "description": "External Threat Actors, SQL injection vulnerability, can manipulate database queries which leads to unauthorized data modification, negatively impacting Database.",
    "target": "Database",
    "source": "External Threat Actors",
    "likelihood": "Medium",
    "impact": "Unauthorized alteration of database records.",
    "mitigations": ["Use parameterized queries", "Deploy database activity monitoring"],
    "prerequisites": ["Unsanitized user input in database queries"],
    "vector": "Malicious SQL code injection"
  }
]}}}
"""

SAMPLE_TOOL_CALL = """
<tool_call>
<function=add_threats>
<parameter=threats>
[{"name": "Session Hijacking", "stride_category": "Spoofing", "description": "External Threat Actors, stolen session token, can impersonate authenticated user which leads to unauthorized account access, negatively impacting Web Application.", "target": "Web Application", "source": "External Threat Actors", "likelihood": "High", "impact": "Unauthorized account access.", "mitigations": ["Secure cookie attributes", "Session rotation"], "prerequisites": ["Stolen session token"], "vector": "Session token reuse"}]
</parameter>
</function>
</tool_call>
"""

SAMPLE_TOOL_REQUEST = """
Some prose before the payload.
[TOOL_REQUEST]
{"name": "ThreatsList", "arguments": {"threats": [
  {"name": "XSS Injection", "stride_category": "Tampering", "description": "External Threat Actors, input validation flaw, can inject cross-site scripting payloads which leads to client-side code execution, negatively impacting Web Application.", "target": "Web Application", "source": "External Threat Actors", "likelihood": "High", "impact": "Client-side code execution.", "mitigations": ["Input validation", "Content Security Policy"], "prerequisites": ["Reflected or stored input"], "vector": "Malicious script injection"}
]}}
[END_TOOL_REQUEST]
"""


def test_parse_add_threats_json_wrapper():
    result = parse_threats_list_from_text(SAMPLE_JSON)
    assert result is not None
    assert len(result.threats) == 1
    assert result.threats[0].target == "Database"


def test_parse_tool_call_xml():
    result = parse_threats_list_from_text(SAMPLE_TOOL_CALL)
    assert result is not None
    assert result.threats[0].stride_category == "Spoofing"


def test_parse_tool_request_marker():
    result = parse_threats_list_from_text(SAMPLE_TOOL_REQUEST)
    assert result is not None
    assert result.threats[0].name == "XSS Injection"


def test_gap_analysis_stop_when_complete():
    catalog = ThreatCatalog()
    stride = [
        "Spoofing",
        "Tampering",
        "Repudiation",
        "Information Disclosure",
        "Denial of Service",
        "Elevation of Privilege",
    ]
    rows = []
    for index in range(8):
        rows.append(
            Threat(
                name=f"Threat {index}",
                stride_category=stride[index % len(stride)],
                description=(
                    f"[Actor] [access] can attack asset {index} which leads to impact, "
                    f"negatively impacting Asset{index % 3}."
                ),
                target=f"Asset{index % 3}",
                source="External Threat Actors",
                likelihood="Medium",
                impact="Impact",
                mitigations=["Control A", "Control B"],
                prerequisites=["Access"],
                vector="Network",
            )
        )
    catalog.add(ThreatsList(threats=rows))
    gap = gap_analysis(catalog, asset_names=["Asset0", "Asset1", "Asset2"])
    assert gap.stop is True
