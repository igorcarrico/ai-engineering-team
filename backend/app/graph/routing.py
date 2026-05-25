"""Conditional routing logic for the workflow.

The only branch in the graph: after the Code Reviewer runs, either loop back for
a refinement pass or finalize. Keeping this as a small pure function makes the
routing trivially unit-testable.
"""

from __future__ import annotations

from app.graph.state import EngineeringTeamState
from app.schemas.enums import ReviewVerdict

ROUTE_REFINE = "refine"
ROUTE_FINALIZE = "finalize"


def route_after_review(state: EngineeringTeamState) -> str:
    """Decide whether to refine again or finalize the run."""
    review = state.get("code_reviewer", {})
    verdict = review.get("verdict", ReviewVerdict.APPROVE.value)
    iteration = int(state.get("iteration", 0))
    max_iterations = int(state.get("max_iterations", 2))

    wants_revision = verdict == ReviewVerdict.REVISE.value
    has_budget = (iteration + 1) < max_iterations

    if wants_revision and has_budget:
        return ROUTE_REFINE
    return ROUTE_FINALIZE
