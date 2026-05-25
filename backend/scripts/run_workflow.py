"""Run the engineering-team workflow from the command line (mock mode).

Exercises the full LangGraph workflow with a print-based event sink — no HTTP
server or database required. Great for demos and for quickly validating the
graph end-to-end.

Usage:
    python scripts/run_workflow.py "Build a SaaS platform for AI financial analytics"
"""

from __future__ import annotations

import asyncio
import os
import sys

# Allow running as a plain script from anywhere (adds backend/ to sys.path).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.events import EventEmitter, EventHub  # noqa: E402
from app.graph.builder import build_team_graph
from app.graph.state import initial_state
from app.llm.mock_provider import MockProvider

DEFAULT_IDEA = "Build a SaaS platform for AI-powered financial analytics"


async def run(idea: str) -> None:
    hub = EventHub()

    async def printer(event) -> None:  # noqa: ANN001
        who = event.agent.label if event.agent else "system"
        print(f"  [{who:<18}] {event.message}")

    emitter = EventEmitter("cli-run", hub, on_persist=printer)
    provider = MockProvider(latency_seconds=0.15)  # snappy for the CLI
    graph = build_team_graph()

    state = initial_state(
        run_id="cli-run",
        idea=idea,
        name=None,
        constraints="",
        provider="mock",
        model=provider.model,
        max_iterations=2,
    )
    config = {
        "configurable": {
            "thread_id": "cli-run",
            "provider": provider,
            "emitter": emitter,
            "agent_max_retries": 2,
        },
        "recursion_limit": 60,
    }

    print(f"\n>>  Idea: {idea}\n" + "-" * 72)
    final: dict = dict(state)
    async for snapshot in graph.astream(state, config, stream_mode="values"):
        final = snapshot

    print("-" * 72)
    print("[OK] Run complete")
    print(f"    Iterations : {final.get('iteration', 0) + 1}")
    print(f"    Verdict    : {final.get('code_reviewer', {}).get('verdict')}")
    print(f"    Score      : {final.get('review_score')}/100")
    print(f"    Artifacts  : {len(final.get('artifacts', []))}")
    print()


if __name__ == "__main__":
    idea = " ".join(sys.argv[1:]) or DEFAULT_IDEA
    asyncio.run(run(idea))
