"""Run endpoints: detail, event log, and the live SSE stream."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.deps import get_project_service
from app.core.events import hub
from app.db.session import get_session
from app.repositories.run_repo import RunRepository
from app.schemas.run import RunDetail
from app.services.project_service import (
    ProjectService,
    RunNotFound,
    _event_to_dict,
)

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/{run_id}", response_model=RunDetail)
async def get_run(
    run_id: str,
    svc: ProjectService = Depends(get_project_service),
) -> RunDetail:
    try:
        return await svc.get_run_detail(run_id)
    except RunNotFound as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@router.get("/{run_id}/events")
async def get_run_events(
    run_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    events = await RunRepository(session).list_events(run_id)
    return [_event_to_dict(e) for e in events]


@router.get("/{run_id}/stream")
async def stream_run(
    run_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Server-Sent Events stream of a run's activity.

    Subscribes to the live hub *first*, then replays everything already emitted
    (from the in-memory buffer, or the database after a restart), de-duplicating
    by event id. This guarantees a late-joining client sees the full timeline
    with no gaps and then continues live until the run finishes.
    """
    run = await RunRepository(session).get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    persisted = await RunRepository(session).list_events(run_id)

    async def generator():
        async with hub.subscribe(run_id) as queue:
            seen: set[str] = set()

            # 1) Replay from the in-memory buffer if present, else from the DB.
            buffered = hub.buffer(run_id)
            if buffered:
                for event in buffered:
                    seen.add(event.id)
                    yield {"data": json.dumps(event.sse_dict())}
            else:
                for event in persisted:
                    seen.add(event.id)
                    yield {"data": json.dumps(_event_to_dict(event))}

            # 2) If the run already finished, the replay is the whole story.
            if not hub.is_active(run_id):
                yield {"event": "done", "data": json.dumps({"run_id": run_id})}
                return

            # 3) Otherwise stream live until the finish sentinel.
            while True:
                if await request.is_disconnected():
                    break
                event = await queue.get()
                if event is None:  # finish sentinel
                    break
                if event.id in seen:
                    continue
                seen.add(event.id)
                yield {"data": json.dumps(event.sse_dict())}

            yield {"event": "done", "data": json.dumps({"run_id": run_id})}

    return EventSourceResponse(generator())
