"""In-process event hub + emitter powering the live activity stream.

The hub is a tiny pub/sub: each run keeps an in-memory buffer (for replay of a
run already in progress) and a set of subscriber queues (for live streaming).
Durable replay of *finished* runs comes from the database, not the hub.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from app.schemas.enums import AgentRole, EventType
from app.schemas.events import RunEvent

OnEvent = Callable[[RunEvent], Awaitable[None]]


class EventHub:
    """Process-wide pub/sub for run events."""

    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[RunEvent | None]]] = {}
        self._buffers: dict[str, list[RunEvent]] = {}
        self._finished: set[str] = set()
        self._lock = asyncio.Lock()

    async def publish(self, event: RunEvent) -> None:
        async with self._lock:
            self._buffers.setdefault(event.run_id, []).append(event)
            subscribers = list(self._subscribers.get(event.run_id, ()))
        for queue in subscribers:
            queue.put_nowait(event)

    async def finish(self, run_id: str) -> None:
        """Signal all current subscribers that the run has ended."""
        async with self._lock:
            self._finished.add(run_id)
            subscribers = list(self._subscribers.get(run_id, ()))
        for queue in subscribers:
            queue.put_nowait(None)  # sentinel

    def is_active(self, run_id: str) -> bool:
        return run_id in self._buffers and run_id not in self._finished

    def buffer(self, run_id: str) -> list[RunEvent]:
        return list(self._buffers.get(run_id, ()))

    @asynccontextmanager
    async def subscribe(self, run_id: str) -> AsyncIterator[asyncio.Queue[RunEvent | None]]:
        queue: asyncio.Queue[RunEvent | None] = asyncio.Queue()
        async with self._lock:
            self._subscribers.setdefault(run_id, set()).add(queue)
        try:
            yield queue
        finally:
            async with self._lock:
                subs = self._subscribers.get(run_id)
                if subs:
                    subs.discard(queue)
                    if not subs:
                        self._subscribers.pop(run_id, None)


class EventEmitter:
    """Convenience wrapper used by graph nodes to emit typed events.

    Each emitted event is first persisted (via ``on_persist``) and then published
    to the hub, so the live stream and the durable log never diverge.
    """

    def __init__(self, run_id: str, hub: EventHub, on_persist: OnEvent | None = None) -> None:
        self.run_id = run_id
        self._hub = hub
        self._on_persist = on_persist

    async def emit(
        self,
        type: EventType,
        message: str,
        *,
        agent: AgentRole | None = None,
        iteration: int = 0,
        data: dict | None = None,
    ) -> RunEvent:
        event = RunEvent(
            run_id=self.run_id,
            type=type,
            agent=agent,
            message=message,
            iteration=iteration,
            data=data or {},
        )
        if self._on_persist is not None:
            await self._on_persist(event)
        await self._hub.publish(event)
        return event


# Single process-wide hub instance.
hub = EventHub()
