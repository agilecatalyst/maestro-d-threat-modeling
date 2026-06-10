"""LangGraph orchestration for the threat modeling pipeline."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from assets_worker import run_assets
from flows_worker import run_flows
from summary_worker import run_summary
from threats_worker import run_finalize, run_threats
from workflow_state import PipelineState


def _summary_node(state: PipelineState) -> dict:
    run_summary(state["job_id"], state.get("diagram_path"), state.get("description"))
    return {}


def _assets_node(state: PipelineState) -> dict:
    run_assets(
        state["job_id"],
        state.get("description"),
        state.get("application_type"),
    )
    return {}


def _flows_node(state: PipelineState) -> dict:
    run_flows(state["job_id"], state.get("description"))
    return {}


def _threats_node(state: PipelineState) -> dict:
    run_threats(state["job_id"], state.get("description"))
    return {}


def _finalize_node(state: PipelineState) -> dict:
    run_finalize(state["job_id"])
    return {}


_builder = StateGraph(PipelineState)
_builder.add_node("summary", _summary_node)
_builder.add_node("assets", _assets_node)
_builder.add_node("flows", _flows_node)
_builder.add_node("threats", _threats_node)
_builder.add_node("finalize", _finalize_node)
_builder.set_entry_point("summary")
_builder.add_edge("summary", "assets")
_builder.add_edge("assets", "flows")
_builder.add_edge("flows", "threats")
_builder.add_edge("threats", "finalize")
_builder.add_edge("finalize", END)
pipeline_graph = _builder.compile()
