"""Persistence for projects."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.db import Project, Run


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(self, *, name: str, idea: str, constraints: str = "") -> Project:
        project = Project(name=name, idea=idea, constraints=constraints)
        self._s.add(project)
        await self._s.flush()
        return project

    async def get(self, project_id: str) -> Project | None:
        stmt = select(Project).where(Project.id == project_id).options(selectinload(Project.runs))
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def list(self) -> list[Project]:
        stmt = (
            select(Project)
            .options(selectinload(Project.runs).selectinload(Run.artifacts))
            .order_by(Project.created_at.desc())
        )
        return list((await self._s.execute(stmt)).scalars().all())

    async def latest_run(self, project_id: str) -> Run | None:
        stmt = select(Run).where(Run.project_id == project_id).order_by(Run.created_at.desc()).limit(1)
        return (await self._s.execute(stmt)).scalar_one_or_none()
