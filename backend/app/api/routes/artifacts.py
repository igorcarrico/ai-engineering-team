"""Artifact endpoints: list, tree, detail and exports (md / json / zip)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from app.api.deps import get_artifact_service
from app.schemas.artifact import ArtifactRead, WorkspaceTree
from app.services.artifact_service import ArtifactService

router = APIRouter(tags=["artifacts"])


@router.get("/runs/{run_id}/artifacts", response_model=list[ArtifactRead])
async def list_artifacts(
    run_id: str,
    svc: ArtifactService = Depends(get_artifact_service),
) -> list[ArtifactRead]:
    return await svc.list_for_run(run_id)


@router.get("/runs/{run_id}/tree", response_model=WorkspaceTree)
async def workspace_tree(
    run_id: str,
    svc: ArtifactService = Depends(get_artifact_service),
) -> WorkspaceTree:
    return await svc.tree_for_run(run_id)


@router.get("/artifacts/{artifact_id}", response_model=ArtifactRead)
async def get_artifact(
    artifact_id: str,
    svc: ArtifactService = Depends(get_artifact_service),
) -> ArtifactRead:
    artifact = await svc.get(artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@router.get("/runs/{run_id}/export.md", response_class=PlainTextResponse)
async def export_markdown(
    run_id: str,
    svc: ArtifactService = Depends(get_artifact_service),
) -> PlainTextResponse:
    content = await svc.export_markdown(run_id)
    return PlainTextResponse(
        content,
        headers={"Content-Disposition": f'attachment; filename="run-{run_id}.md"'},
    )


@router.get("/runs/{run_id}/export.json")
async def export_json(
    run_id: str,
    svc: ArtifactService = Depends(get_artifact_service),
) -> JSONResponse:
    payload = await svc.export_json(run_id)
    return JSONResponse(
        payload,
        headers={"Content-Disposition": f'attachment; filename="run-{run_id}.json"'},
    )


@router.get("/runs/{run_id}/export.zip")
async def export_zip(
    run_id: str,
    svc: ArtifactService = Depends(get_artifact_service),
) -> Response:
    data = await svc.export_zip(run_id)
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="workspace-{run_id}.zip"'},
    )
