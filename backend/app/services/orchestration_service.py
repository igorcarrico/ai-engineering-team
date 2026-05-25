"""Drives a workflow run: executes the graph, streams events, persists state.

This service is the bridge between the (pure) LangGraph workflow and the
(stateful) outside world. It:

* injects the provider + emitter into the graph via ``config``,
* consumes ``astream`` snapshots to persist progress between supersteps,
* persists every emitted event for durable replay, and
* finalizes the run (status, score, summary, timing) when the graph ends.

Each database write uses its own short-lived session so the concurrent writes
from parallel graph nodes never share a session.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from app.config import settings
from app.core.events import EventEmitter, EventHub
from app.db.session import AsyncSessionLocal
from app.graph.builder import build_team_graph
from app.graph.state import initial_state
from app.llm.factory import build_provider
from app.logging_config import get_logger
from app.repositories.artifact_repo import ArtifactRepository
from app.repositories.run_repo import RunRepository
from app.schemas.enums import AgentRole, EventType
from app.schemas.events import RunEvent

log = get_logger(__name__)

_OUTPUT_KEYS = (
    "product_manager",
    "architect",
    "backend_engineer",
    "frontend_engineer",
    "qa_engineer",
    "security_reviewer",
    "code_reviewer",
)


def _extract_outputs(state: dict[str, Any]) -> dict[str, Any]:
    return {k: state[k] for k in _OUTPUT_KEYS if k in state}


class OrchestrationService:
    """Owns the compiled graph and executes runs against it."""

    def __init__(self, hub: EventHub) -> None:
        self._hub = hub
        self._graph = build_team_graph()
        self._tasks: dict[str, asyncio.Task] = {}

    # --- Public API ------------------------------------------------------- #

    def launch(
        self,
        *,
        run_id: str,
        idea: str,
        name: str | None,
        constraints: str,
        provider: str,
        model: str,
        max_iterations: int,
    ) -> asyncio.Task:
        """Start a run as a background task and return it."""
        task = asyncio.create_task(
            self._run(
                run_id=run_id,
                idea=idea,
                name=name,
                constraints=constraints,
                provider=provider,
                model=model,
                max_iterations=max_iterations,
            )
        )
        self._tasks[run_id] = task
        task.add_done_callback(lambda _t: self._tasks.pop(run_id, None))
        return task

    # --- Internal --------------------------------------------------------- #

    async def _run(
        self,
        *,
        run_id: str,
        idea: str,
        name: str | None,
        constraints: str,
        provider: str,
        model: str,
        max_iterations: int,
    ) -> None:
        emitter = EventEmitter(run_id, self._hub, on_persist=self._persist_event)
        llm = build_provider(provider, model)  # type: ignore[arg-type]
        started = time.perf_counter()

        await self._set_running(run_id)
        await emitter.emit(
            EventType.RUN_STARTED,
            f"Engineering team assembled. Provider: {llm.name} · model: {llm.model}.",
            agent=AgentRole.SUPERVISOR,
            data={"provider": llm.name, "model": llm.model},
        )

        state = initial_state(
            run_id=run_id,
            idea=idea,
            name=name,
            constraints=constraints,
            provider=llm.name,
            model=llm.model,
            max_iterations=max_iterations,
        )
        config = {
            "configurable": {
                "thread_id": run_id,
                "provider": llm,
                "emitter": emitter,
                "agent_max_retries": settings.agent_max_retries,
            },
            "recursion_limit": 60,
        }

        final_state: dict[str, Any] = dict(state)
        try:
            async for snapshot in self._graph.astream(state, config, stream_mode="values"):
                final_state = snapshot
                await self._persist_progress(run_id, snapshot)

            duration_ms = int((time.perf_counter() - started) * 1000)
            await self._finalize(run_id, final_state, duration_ms)
            log.info("run_completed", run_id=run_id, duration_ms=duration_ms)
        except Exception as exc:  # noqa: BLE001
            duration_ms = int((time.perf_counter() - started) * 1000)
            log.exception("run_failed", run_id=run_id)
            await emitter.emit(
                EventType.RUN_FAILED,
                f"Run failed: {exc}",
                agent=AgentRole.SUPERVISOR,
                data={"error": str(exc)},
            )
            await self._fail(run_id, str(exc), duration_ms)
        finally:
            await self._hub.finish(run_id)

    async def _persist_event(self, event: RunEvent) -> None:
        async with AsyncSessionLocal() as session:
            await RunRepository(session).add_event(event)
            await session.commit()

    async def _persist_progress(self, run_id: str, snapshot: dict[str, Any]) -> None:
        async with AsyncSessionLocal() as session:
            await RunRepository(session).update_progress(
                run_id,
                outputs=_extract_outputs(snapshot),
                iteration=int(snapshot.get("iteration", 0)),
            )
            await ArtifactRepository(session).replace_for_run(run_id, snapshot.get("artifacts", []))
            await session.commit()

    async def _set_running(self, run_id: str) -> None:
        async with AsyncSessionLocal() as session:
            await RunRepository(session).set_status(run_id, "running")
            await session.commit()

    async def _finalize(self, run_id: str, state: dict[str, Any], duration_ms: int) -> None:
        review = state.get("code_reviewer", {})
        async with AsyncSessionLocal() as session:
            await RunRepository(session).finalize(
                run_id,
                status="completed",
                outputs=_extract_outputs(state),
                iteration=int(state.get("iteration", 0)),
                review_score=review.get("score"),
                final_summary=state.get("final_summary"),
                duration_ms=duration_ms,
            )
            await ArtifactRepository(session).replace_for_run(run_id, state.get("artifacts", []))
            await session.commit()

    async def _fail(self, run_id: str, error: str, duration_ms: int) -> None:
        async with AsyncSessionLocal() as session:
            await RunRepository(session).finalize(
                run_id,
                status="failed",
                outputs={},
                iteration=0,
                review_score=None,
                final_summary=None,
                duration_ms=duration_ms,
                error=error,
            )
            await session.commit()
