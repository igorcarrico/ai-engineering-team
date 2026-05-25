"""Conditional routing after the code review."""

from __future__ import annotations

from app.graph.routing import ROUTE_FINALIZE, ROUTE_REFINE, route_after_review


def _state(verdict: str, iteration: int, max_iterations: int = 2) -> dict:
    return {
        "code_reviewer": {"verdict": verdict},
        "iteration": iteration,
        "max_iterations": max_iterations,
    }


def test_revise_with_budget_refines():
    assert route_after_review(_state("revise", iteration=0, max_iterations=2)) == ROUTE_REFINE


def test_revise_without_budget_finalizes():
    assert route_after_review(_state("revise", iteration=1, max_iterations=2)) == ROUTE_FINALIZE


def test_approve_finalizes():
    assert route_after_review(_state("approve", iteration=0, max_iterations=2)) == ROUTE_FINALIZE


def test_single_iteration_never_refines():
    assert route_after_review(_state("revise", iteration=0, max_iterations=1)) == ROUTE_FINALIZE
