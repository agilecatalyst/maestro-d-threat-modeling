"""Verify LangGraph pipeline wiring (no LLM)."""

import sys
from pathlib import Path
from unittest.mock import patch

AGENT_DIR = Path(__file__).resolve().parent.parent / "backend" / "agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from workflow_graph import pipeline_graph


def test_pipeline_graph_has_expected_nodes():
    node_names = set(pipeline_graph.get_graph().nodes.keys())
    for expected in ("summary", "assets", "flows", "threats", "finalize"):
        assert expected in node_names


def test_pipeline_graph_invoke_calls_workers():
    calls = []

    with patch("workflow_graph.run_summary", side_effect=lambda *a, **k: calls.append("summary")), patch(
        "workflow_graph.run_assets", side_effect=lambda *a, **k: calls.append("assets")
    ), patch("workflow_graph.run_flows", side_effect=lambda *a, **k: calls.append("flows")), patch(
        "workflow_graph.run_threats", side_effect=lambda *a, **k: calls.append("threats")
    ), patch(
        "workflow_graph.run_finalize", side_effect=lambda *a, **k: calls.append("finalize")
    ):
        pipeline_graph.invoke(
            {
                "job_id": "test-job",
                "diagram_path": "diagrams/x.png",
                "description": "desc",
                "application_type": "hybrid",
            }
        )

    assert calls == ["summary", "assets", "flows", "threats", "finalize"]
