"""Persistence for the post-run conversation."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import Message


class ChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(
        self,
        *,
        run_id: str,
        role: str,
        content: str,
        agent: str | None = None,
    ) -> Message:
        message = Message(run_id=run_id, role=role, content=content, agent=agent)
        self._s.add(message)
        await self._s.flush()
        return message

    async def list(self, run_id: str) -> list[Message]:
        stmt = select(Message).where(Message.run_id == run_id).order_by(Message.seq)
        return list((await self._s.execute(stmt)).scalars().all())
