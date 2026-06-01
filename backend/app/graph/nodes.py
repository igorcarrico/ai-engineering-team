"""Graph node functions.

Each agent is wrapped in a node that owns the orchestration concerns the agent
itself shouldn't care about: emitting lifecycle events, retrying transient
failures, timing, and translating the agent result into a state delta.
Provider and emitter are injected through the LangGraph ``config`` so the same
graph can run against mock or real providers and against any event sink.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from langchain_core.runnables import RunnableConfig

from app.agents.registry import get_agent
from app.core.events import EventEmitter
from app.graph.state import EngineeringTeamState
from app.llm.base import LLMProvider
from app.logging_config import get_logger
from app.schemas.enums import AgentRole, EventType, ReviewVerdict

log = get_logger(__name__)

_PROGRESS_DELAY = 0.15  # seconds between streamed progress steps (cinematic feel)


def _deps(config: RunnableConfig) -> tuple[LLMProvider, EventEmitter, int]:
    cfg = config.get("configurable", {})
    return cfg["provider"], cfg["emitter"], int(cfg.get("agent_max_retries", 2))


async def _invoke_with_retry(agent, provider, ctx, emitter, max_retries: int):
    """Invoke an agent, emitting retry events on transient failures."""
    attempts = max_retries + 1
    for attempt in range(1, attempts + 1):
        try:
            return await agent.invoke(provider, ctx)
        except Exception as exc:  # noqa: BLE001 - we surface the error as an event
            log.warning("agent_invoke_failed", agent=agent.role.value, attempt=attempt, error=str(exc))
            if attempt >= attempts:
                raise
            await emitter.emit(
                EventType.AGENT_RETRY,
                f"{agent.title} hit a transient error — retrying ({attempt}/{max_retries})...",
                agent=agent.role,
                iteration=int(ctx.get("iteration", 0)),
                data={"attempt": attempt, "error": str(exc)},
            )
            await asyncio.sleep(0.4 * attempt)


def make_agent_node(agent_key: str):
    """Build an async LangGraph node for the given agent key."""
    agent = get_agent(agent_key)

    async def node(state: EngineeringTeamState, config: RunnableConfig) -> dict[str, Any]:
        provider, emitter, max_retries = _deps(config)
        iteration = int(state.get("iteration", 0))
        ctx = dict(state)

        await emitter.emit(
            EventType.AGENT_STARTED,
            f"{agent.title} started working.",
            agent=agent.role,
            iteration=iteration,
        )

        for step in agent.progress_steps(ctx):
            await emitter.emit(EventType.AGENT_PROGRESS, step, agent=agent.role, iteration=iteration)
            await asyncio.sleep(_PROGRESS_DELAY)

        started = time.perf_counter()
        try:
            output = await _invoke_with_retry(agent, provider, ctx, emitter, max_retries)
        except Exception as exc:  # noqa: BLE001
            await emitter.emit(
                EventType.AGENT_FAILED,
                f"{agent.title} failed after retries: {exc}",
                agent=agent.role,
                iteration=iteration,
                data={"error": str(exc)},
            )
            raise

        artifacts = agent.build_artifacts(output, ctx)
        artifact_dicts = [a.model_dump(mode="json") for a in artifacts]
        for art in artifacts:
            await emitter.emit(
                EventType.ARTIFACT_CREATED,
                f"{agent.title} produced “{art.title}”.",
                agent=agent.role,
                iteration=iteration,
                data={"title": art.title, "path": art.path, "kind": art.kind.value},
            )

        duration_ms = int((time.perf_counter() - started) * 1000)
        completed_data: dict[str, Any] = {"duration_ms": duration_ms, "artifacts": len(artifacts)}
        if agent.role is AgentRole.CODE_REVIEWER:
            completed_data["verdict"] = output.verdict.value  # type: ignore[attr-defined]
            completed_data["score"] = output.score  # type: ignore[attr-defined]

        await emitter.emit(
            EventType.AGENT_COMPLETED,
            f"{agent.title} completed.",
            agent=agent.role,
            iteration=iteration,
            data=completed_data,
        )

        delta: dict[str, Any] = {
            agent_key: output.model_dump(mode="json"),
            "artifacts": artifact_dicts,
        }
        if agent.role is AgentRole.CODE_REVIEWER:
            delta["review_score"] = output.score  # type: ignore[attr-defined]
            delta["revision_focus"] = list(output.revision_focus)  # type: ignore[attr-defined]
        return delta

    node.__name__ = f"{agent_key}_node"
    return node


async def refine_node(state: EngineeringTeamState, config: RunnableConfig) -> dict[str, Any]:
    """Increment the iteration counter and announce a refinement pass."""
    _, emitter, _ = _deps(config)
    next_iteration = int(state.get("iteration", 0)) + 1
    focus = state.get("revision_focus", [])
    await emitter.emit(
        EventType.ITERATION_STARTED,
        f"Refinement pass #{next_iteration} started — addressing reviewer feedback.",
        agent=AgentRole.SUPERVISOR,
        iteration=next_iteration,
        data={"revision_focus": focus},
    )
    return {"iteration": next_iteration}


async def finalize_node(state: EngineeringTeamState, config: RunnableConfig) -> dict[str, Any]:
    """Compose the executive delivery summary and close out the run."""
    _, emitter, _ = _deps(config)
    iteration = int(state.get("iteration", 0))
    review = state.get("code_reviewer", {})
    summary = _build_summary(state)

    from app.schemas.artifact import ArtifactBase  # local import avoids cycle
    from app.schemas.enums import ArtifactKind

    summary_artifact = ArtifactBase(
        title="Feasibility Study Summary",
        path="docs/00-delivery-summary.md",
        kind=ArtifactKind.DOCUMENT,
        produced_by=AgentRole.SUPERVISOR,
        content=summary,
        summary="Executive verdict for the founder — GO/NO-GO, timeline, budget",
    )

    verdict = review.get("verdict", ReviewVerdict.APPROVE.value)
    await emitter.emit(
        EventType.RUN_COMPLETED,
        f"Run completed — final verdict: {verdict.upper()} (score {review.get('score', 'n/a')}/100).",
        agent=AgentRole.SUPERVISOR,
        iteration=iteration,
        data={"verdict": verdict, "score": review.get("score")},
    )
    return {
        "status": "completed",
        "final_summary": summary,
        "artifacts": [summary_artifact.model_dump(mode="json")],
    }


def _build_summary(state: EngineeringTeamState) -> str:
    pm = state.get("product_manager", {})
    arch = state.get("architect", {})
    be = state.get("backend_engineer", {})
    fe = state.get("frontend_engineer", {})
    review = state.get("code_reviewer", {})
    sec = state.get("security_reviewer", {})
    name = state.get("name") or "the idea"
    # De-duplicate by path so the summary matches the persisted workspace.
    unique = {a.get("path"): a for a in state.get("artifacts", [])}
    artifacts = list(unique.values())

    go_no_go = (review.get("go_no_go") or "").upper() or "—"
    verdict_rationale = review.get("verdict_rationale") or review.get("overall_assessment", "")
    mvp_t = review.get("mvp_timeline") or "—"
    mvp_b = review.get("mvp_budget_usd_range") or "—"
    v1_t = review.get("v1_timeline") or "—"
    v1_b = review.get("v1_budget_usd_range") or "—"

    lines = [
        f"# Feasibility Study — {name}",
        "",
        f"> _Founder's idea:_ {state.get('idea', '')}",
        "",
        "## Recommendation",
        f"# `{go_no_go}`",
        "",
        verdict_rationale or "_No rationale provided._",
        "",
        "## Timeline & Budget",
        "",
        "| Stage | Timeline | Budget |",
        "|---|---|---|",
        f"| **MVP** | {mvp_t} | {mvp_b} |",
        f"| **V1 (polished)** | {v1_t} | {v1_b} |",
        "",
    ]

    if pm.get("value_proposition"):
        lines += ["## Value Proposition", f"> {pm['value_proposition']}", ""]
    if pm.get("primary_metric_target"):
        lines += ["## Primary Metric", f"**{pm['primary_metric_target']}**", ""]

    if review.get("recommended_team"):
        lines += ["## Recommended Team", review["recommended_team"], ""]

    if review.get("top_questions_to_validate_first"):
        lines += [
            "## Validate Before Committing Budget",
            *[f"- {q}" for q in review["top_questions_to_validate_first"]],
            "",
        ]

    if review.get("kill_criteria"):
        lines += [
            "## Kill Criteria — when to abandon",
            *[f"- {k}" for k in review["kill_criteria"]],
            "",
        ]

    lines += [
        "## Behind the verdict",
        f"- **Architecture complexity:** {arch.get('complexity_rating', arch.get('architecture_style', 'n/a'))}",
        f"- **Backend effort:** {be.get('effort_estimate') or 'n/a'} — {be.get('team_needed') or '—'}",
        f"- **Frontend effort:** {fe.get('effort_estimate') or 'n/a'} — {fe.get('team_needed') or '—'}",
        f"- **Compliance specialist required:** {'yes' if sec.get('requires_specialist') else 'no'}",
        f"- **Plan quality score:** {review.get('score', 'n/a')}/100 ({review.get('verdict', 'n/a')})",
        f"- **Refinement iterations:** {int(state.get('iteration', 0)) + 1}",
        f"- **Artifacts produced:** {len(artifacts)}",
        "",
        "_Generated by the AI Engineering Team — multi-agent feasibility consultancy._",
    ]
    return "\n".join(lines)
