"""Chat DTOs for the post-run conversational mode."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.enums import AgentRole


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    agent: AgentRole | None = Field(
        default=None,
        description="Target a specific agent. None routes to the Lead Consultant (the team).",
    )


class ChatMessageRead(BaseModel):
    id: str
    seq: int
    run_id: str
    role: Literal["user", "assistant"]
    agent: AgentRole | None
    agent_label: str | None
    content: str
    created_at: datetime


class ChatExchange(BaseModel):
    """Returned by POST: the user message just persisted + the agent's reply."""

    user: ChatMessageRead
    assistant: ChatMessageRead
