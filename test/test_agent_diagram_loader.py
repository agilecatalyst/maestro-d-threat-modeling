import sys
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent.parent / "backend" / "agent"
if not (AGENT_DIR / "diagram_loader.py").exists():
    AGENT_DIR = Path("/agent")
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from diagram_loader import load_diagram_data_url


def test_agent_load_diagram_rejects_traversal():
    assert load_diagram_data_url("../../etc/passwd") is None


def test_agent_load_diagram_rejects_absolute():
    assert load_diagram_data_url("/etc/passwd") is None
