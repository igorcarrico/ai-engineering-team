"""Assembles the multi-agent workflow into a compiled LangGraph.

Topology
--------
    START → product_manager → architect ─┬─→ backend_engineer ─┐
                                         └─→ frontend_engineer ─┴─→ qa_engineer
        → security_reviewer → code_reviewer ─(conditional)─┬─ refine → architect
                                                           └─ finalize → END

* ``architect`` fans out to the two engineers in parallel; ``qa_engineer`` is a
  join that waits for both.
* ``code_reviewer`` is the only branch point: it either loops back through
  ``refine`` (bounded by ``max_iterations``) or proceeds to ``finalize``.
* A checkpointer makes runs resumable/replayable per ``thread_id``.
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.graph.nodes import finalize_node, make_agent_node, refine_node
from app.graph.routing import ROUTE_FINALIZE, ROUTE_REFINE, route_after_review
from app.graph.state import EngineeringTeamState


def build_team_graph(checkpointer: object | None = None) -> CompiledStateGraph:
    """Build and compile the engineering-team workflow graph."""
    graph = StateGraph(EngineeringTeamState)

    # Agent nodes
    graph.add_node("product_manager", make_agent_node("product_manager"))
    graph.add_node("architect", make_agent_node("architect"))
    graph.add_node("backend_engineer", make_agent_node("backend_engineer"))
    graph.add_node("frontend_engineer", make_agent_node("frontend_engineer"))
    graph.add_node("qa_engineer", make_agent_node("qa_engineer"))
    graph.add_node("security_reviewer", make_agent_node("security_reviewer"))
    graph.add_node("code_reviewer", make_agent_node("code_reviewer"))

    # Control nodes
    graph.add_node("refine", refine_node)
    graph.add_node("finalize", finalize_node)

    # Linear intro
    graph.add_edge(START, "product_manager")
    graph.add_edge("product_manager", "architect")

    # Parallel fan-out to the two engineers
    graph.add_edge("architect", "backend_engineer")
    graph.add_edge("architect", "frontend_engineer")

    # Join: qa_engineer waits for BOTH engineers
    graph.add_edge("backend_engineer", "qa_engineer")
    graph.add_edge("frontend_engineer", "qa_engineer")

    # Review chain
    graph.add_edge("qa_engineer", "security_reviewer")
    graph.add_edge("security_reviewer", "code_reviewer")

    # Conditional branch: refine or finalize
    graph.add_conditional_edges(
        "code_reviewer",
        route_after_review,
        {ROUTE_REFINE: "refine", ROUTE_FINALIZE: "finalize"},
    )
    graph.add_edge("refine", "architect")  # loop back
    graph.add_edge("finalize", END)

    return graph.compile(checkpointer=checkpointer or MemorySaver())
