"""Event schema for the live activity stream.

A `RunEvent` is the atomic unit of observability: every meaningful thing the
graph does emits one. They are streamed to the UI over SSE *and* persisted so a
run can be replayed after the fact.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.schemas.enums import AgentRole, EventType


def _now() -> datetime:
    return datetime.now(UTC)


class RunEvent(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    run_id: str
    type: EventType
    agent: AgentRole | None = None
    message: str
    iteration: int = 0
    # Free-form structured payload (e.g. artifact id, score, routing target).
    data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)

    def sse_dict(self) -> dict[str, Any]:
        """Serializable form sent to the browser."""
        return {
            "id": self.id,
            "run_id": self.run_id,
            "type": self.type.value,
            "agent": self.agent.value if self.agent else None,
            "agent_label": self.agent.label if self.agent else None,
            "message": self.message,
            "iteration": self.iteration,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
        }
