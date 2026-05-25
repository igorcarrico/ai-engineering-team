"""The shared, stateful object that flows through the LangGraph workflow.

Only ``artifacts`` uses a reducer (list concatenation) because parallel nodes
append to it. Every other field is written by exactly one node per superstep, so
last-write-wins is correct and intentional (e.g. a refine pass overwrites the
architect's previous output while artifacts accumulate as history).
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class EngineeringTeamState(TypedDict, total=False):
    # --- Inputs ---
    run_id: str
    idea: str
    name: str | None
    constraints: str
    provider: str
    model: str

    # --- Iteration control ---
    iteration: int
    max_iterations: int
    revision_focus: list[str]

    # --- Per-agent structured outputs (JSON-serializable dicts) ---
    product_manager: dict[str, Any]
    architect: dict[str, Any]
    backend_engineer: dict[str, Any]
    frontend_engineer: dict[str, Any]
    qa_engineer: dict[str, Any]
    security_reviewer: dict[str, Any]
    code_reviewer: dict[str, Any]

    # --- Accumulated artifacts (reducer: concatenated across nodes) ---
    artifacts: Annotated[list[dict[str, Any]], operator.add]

    # --- Outputs / control ---
    status: str
    review_score: int
    final_summary: str


def initial_state(
    *,
    run_id: str,
    idea: str,
    name: str | None,
    constraints: str,
    provider: str,
    model: str,
    max_iterations: int,
) -> EngineeringTeamState:
    return EngineeringTeamState(
        run_id=run_id,
        idea=idea,
        name=name,
        constraints=constraints,
        provider=provider,
        model=model,
        iteration=0,
        max_iterations=max_iterations,
        revision_focus=[],
        artifacts=[],
        status="running",
    )
