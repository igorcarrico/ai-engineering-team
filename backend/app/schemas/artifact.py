"""Artifact schemas — the tangible deliverables produced during a run."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.enums import AgentRole, ArtifactKind


class ArtifactBase(BaseModel):
    title: str
    path: str = Field(description="Virtual path within the run workspace")
    kind: ArtifactKind
    language: str = "markdown"
    produced_by: AgentRole
    content: str
    summary: str = ""


class ArtifactRead(ArtifactBase):
    id: str
    run_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ArtifactTreeNode(BaseModel):
    """A node in the workspace file tree returned to the artifact explorer."""

    name: str
    path: str
    is_dir: bool
    kind: ArtifactKind | None = None
    artifact_id: str | None = None
    children: list[ArtifactTreeNode] = Field(default_factory=list)


class WorkspaceTree(BaseModel):
    root: ArtifactTreeNode
    total_files: int
    by_kind: dict[str, int] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


ArtifactTreeNode.model_rebuild()
