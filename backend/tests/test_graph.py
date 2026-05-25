"""End-to-end execution of the LangGraph workflow in mock mode."""

from __future__ import annotations

from app.core.events import EventEmitter, EventHub
from app.graph.builder import build_team_graph
from app.graph.state import initial_state
from app.llm.mock_provider import MockProvider
from app.schemas.enums import EventType


async def _run_graph(idea: str = "Build a SaaS for AI financial analytics"):
    hub = EventHub()
    events = []

    async def collect(event):  # noqa: ANN001
        events.append(event)

    emitter = EventEmitter("test-run", hub, on_persist=collect)
    provider = MockProvider(latency_seconds=0)
    graph = build_team_graph()
    state = initial_state(
        run_id="test-run",
        idea=idea,
        name=None,
        constraints="",
        provider="mock",
        model=provider.model,
        max_iterations=2,
    )
    config = {
        "configurable": {
            "thread_id": "test-run",
            "provider": provider,
            "emitter": emitter,
            "agent_max_retries": 2,
        },
        "recursion_limit": 60,
    }
    final = dict(state)
    async for snapshot in graph.astream(state, config, stream_mode="values"):
        final = snapshot
    return final, events


async def test_graph_completes_and_approves():
    final, events = await _run_graph()
    assert final["status"] == "completed"
    assert final["code_reviewer"]["verdict"] == "approve"
    assert final["review_score"] >= 80


async def test_graph_produces_all_agent_outputs():
    final, _ = await _run_graph()
    for key in (
        "product_manager",
        "architect",
        "backend_engineer",
        "frontend_engineer",
        "qa_engineer",
        "security_reviewer",
        "code_reviewer",
    ):
        assert key in final, f"missing output: {key}"


async def test_graph_performs_one_refinement_iteration():
    final, events = await _run_graph()
    # mock reviewer requests REVISE on iteration 0, then APPROVE -> exactly one loop
    assert final["iteration"] == 1
    iteration_events = [e for e in events if e.type == EventType.ITERATION_STARTED]
    assert len(iteration_events) == 1


async def test_graph_emits_lifecycle_events():
    _, events = await _run_graph()
    types = {e.type for e in events}
    assert EventType.RUN_COMPLETED in types
    assert EventType.AGENT_COMPLETED in types
    assert EventType.ARTIFACT_CREATED in types


async def test_graph_generates_artifacts():
    final, _ = await _run_graph()
    artifacts = final["artifacts"]
    paths = {a["path"] for a in artifacts}
    assert "docs/01-product-definition.md" in paths
    assert "docs/00-delivery-summary.md" in paths
    assert any(a["kind"] == "code" for a in artifacts)
