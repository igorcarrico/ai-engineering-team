"""Persistence for run artifacts (the generated workspace)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import Artifact


class ArtifactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def replace_for_run(self, run_id: str, artifacts: list[dict[str, Any]]) -> None:
        """Replace a run's artifacts, de-duplicating by path (last write wins).

        Refinement passes regenerate documents, so we keep only the latest
        version of each path rather than accumulating duplicates.
        """
        existing = {a.path: a for a in await self.list(run_id)}
        latest: dict[str, dict[str, Any]] = {}
        for art in artifacts:
            latest[art["path"]] = art  # last occurrence wins

        for path, art in latest.items():
            row = existing.get(path)
            if row is None:
                self._s.add(
                    Artifact(
                        run_id=run_id,
                        title=art["title"],
                        path=art["path"],
                        kind=art["kind"],
                        language=art.get("language", "markdown"),
                        produced_by=art["produced_by"],
                        content=art["content"],
                        summary=art.get("summary", ""),
                    )
                )
            else:
                row.title = art["title"]
                row.kind = art["kind"]
                row.language = art.get("language", "markdown")
                row.produced_by = art["produced_by"]
                row.content = art["content"]
                row.summary = art.get("summary", "")
        await self._s.flush()

    async def list(self, run_id: str) -> list[Artifact]:
        stmt = select(Artifact).where(Artifact.run_id == run_id).order_by(Artifact.path)
        return list((await self._s.execute(stmt)).scalars().all())

    async def get(self, artifact_id: str) -> Artifact | None:
        return await self._s.get(Artifact, artifact_id)
