"""Project endpoints: create-and-run, list, detail, rerun."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_project_service
from app.schemas.run import (
    CreateProjectRequest,
    ProjectRead,
    ProjectSummary,
    RunDetail,
)
from app.services.project_service import ProjectNotFound, ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=RunDetail, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: CreateProjectRequest,
    svc: ProjectService = Depends(get_project_service),
) -> RunDetail:
    """Create a project and immediately launch a workflow run."""
    return await svc.create_and_run(body)


@router.get("", response_model=list[ProjectSummary])
async def list_projects(
    svc: ProjectService = Depends(get_project_service),
) -> list[ProjectSummary]:
    return await svc.list_projects()


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: str,
    svc: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    try:
        return await svc.get_project(project_id)
    except ProjectNotFound as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc


@router.post("/{project_id}/rerun", response_model=RunDetail, status_code=status.HTTP_201_CREATED)
async def rerun_project(
    project_id: str,
    svc: ProjectService = Depends(get_project_service),
) -> RunDetail:
    """Start a fresh run for an existing project."""
    try:
        return await svc.rerun(project_id)
    except ProjectNotFound as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
