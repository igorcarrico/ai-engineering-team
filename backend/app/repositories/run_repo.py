"""Persistence for runs and their event log."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.db import Run, RunEvent
from app.schemas.events import RunEvent as RunEventSchema


class RunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(
        self,
        *,
        project_id: str,
        provider: str,
        model: str,
        max_iterations: int,
    ) -> Run:
        run = Run(
            project_id=project_id,
            provider=provider,
            model=model,
            max_iterations=max_iterations,
            status="pending",
            outputs={},
        )
        self._s.add(run)
        await self._s.flush()
        return run

    async def get(self, run_id: str) -> Run | None:
        stmt = select(Run).where(Run.id == run_id).options(selectinload(Run.events), selectinload(Run.artifacts))
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def set_status(self, run_id: str, status: str, *, error: str | None = None) -> None:
        run = await self._s.get(Run, run_id)
        if run is None:
            return
        run.status = status
        if error is not None:
            run.error = error
        await self._s.flush()

    async def update_progress(self, run_id: str, *, outputs: dict[str, Any], iteration: int) -> None:
        run = await self._s.get(Run, run_id)
        if run is None:
            return
        run.outputs = outputs
        run.iteration = iteration
        run.status = "running"
        await self._s.flush()

    async def finalize(
        self,
        run_id: str,
        *,
        status: str,
        outputs: dict[str, Any],
        iteration: int,
        review_score: int | None,
        final_summary: str | None,
        duration_ms: int,
        error: str | None = None,
    ) -> None:
        run = await self._s.get(Run, run_id)
        if run is None:
            return
        run.status = status
        run.outputs = outputs
        run.iteration = iteration
        run.review_score = review_score
        run.final_summary = final_summary
        run.duration_ms = duration_ms
        run.error = error
        run.finished_at = datetime.now(UTC)
        await self._s.flush()

    async def add_event(self, event: RunEventSchema) -> None:
        self._s.add(
            RunEvent(
                id=event.id,
                run_id=event.run_id,
                type=event.type.value,
                agent=event.agent.value if event.agent else None,
                message=event.message,
                iteration=event.iteration,
                data=event.data,
                created_at=event.created_at,
            )
        )
        await self._s.flush()

    async def list_events(self, run_id: str) -> list[RunEvent]:
        stmt = select(RunEvent).where(RunEvent.run_id == run_id).order_by(RunEvent.seq)
        return list((await self._s.execute(stmt)).scalars().all())
