"""Artifact queries: workspace tree + export bundles."""

from __future__ import annotations

import io
import json
import zipfile
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import Artifact
from app.repositories.artifact_repo import ArtifactRepository
from app.repositories.run_repo import RunRepository
from app.schemas.artifact import ArtifactRead, ArtifactTreeNode, WorkspaceTree
from app.services.serializers import artifact_to_read


class ArtifactService:
    def __init__(self, session: AsyncSession) -> None:
        self._artifacts = ArtifactRepository(session)
        self._runs = RunRepository(session)

    async def list_for_run(self, run_id: str) -> list[ArtifactRead]:
        return [artifact_to_read(a) for a in await self._artifacts.list(run_id)]

    async def get(self, artifact_id: str) -> ArtifactRead | None:
        artifact = await self._artifacts.get(artifact_id)
        return artifact_to_read(artifact) if artifact else None

    async def tree_for_run(self, run_id: str) -> WorkspaceTree:
        artifacts = await self._artifacts.list(run_id)
        return _build_tree(artifacts)

    async def export_markdown(self, run_id: str) -> str:
        artifacts = await self._artifacts.list(run_id)
        parts: list[str] = [
            "# AI Engineering Team — Run Export",
            f"_Exported {datetime.now(UTC).isoformat()}_",
            "",
        ]
        for art in artifacts:
            parts.append(f"\n\n---\n\n<!-- {art.path} ({art.produced_by}) -->\n")
            if art.kind == "code":
                parts.append(f"### `{art.path}`\n\n```{art.language}\n{art.content}\n```")
            else:
                parts.append(art.content)
        return "\n".join(parts)

    async def export_json(self, run_id: str) -> dict:
        run = await self._runs.get(run_id)
        artifacts = await self._artifacts.list(run_id)
        return {
            "run_id": run_id,
            "status": run.status if run else "unknown",
            "review_score": run.review_score if run else None,
            "exported_at": datetime.now(UTC).isoformat(),
            "outputs": run.outputs if run else {},
            "artifacts": [artifact_to_read(a).model_dump(mode="json") for a in artifacts],
        }

    async def export_zip(self, run_id: str) -> bytes:
        """Bundle the whole virtual workspace into a downloadable zip."""
        artifacts = await self._artifacts.list(run_id)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for art in artifacts:
                zf.writestr(art.path, art.content)
            manifest = {
                "run_id": run_id,
                "files": [{"path": a.path, "produced_by": a.produced_by, "kind": a.kind} for a in artifacts],
            }
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        return buffer.getvalue()


def _build_tree(artifacts: list[Artifact]) -> WorkspaceTree:
    root = ArtifactTreeNode(name="workspace", path="", is_dir=True)
    by_kind: dict[str, int] = {}

    for art in artifacts:
        by_kind[art.kind] = by_kind.get(art.kind, 0) + 1
        segments = art.path.split("/")
        cursor = root
        accumulated = ""
        for i, segment in enumerate(segments):
            accumulated = f"{accumulated}/{segment}".lstrip("/")
            is_leaf = i == len(segments) - 1
            existing = next((c for c in cursor.children if c.name == segment), None)
            if existing is None:
                node = ArtifactTreeNode(
                    name=segment,
                    path=accumulated,
                    is_dir=not is_leaf,
                    kind=art.kind if is_leaf else None,  # type: ignore[arg-type]
                    artifact_id=art.id if is_leaf else None,
                )
                cursor.children.append(node)
                cursor = node
            else:
                cursor = existing

    return WorkspaceTree(root=root, total_files=len(artifacts), by_kind=by_kind)
