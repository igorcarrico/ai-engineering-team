"""Use-case layer for projects and runs (create, read, re-run)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.llm.mock_data import derive
from app.repositories.project_repo import ProjectRepository
from app.repositories.run_repo import RunRepository
from app.schemas.run import (
    CreateProjectRequest,
    ProjectRead,
    ProjectSummary,
    RunDetail,
    RunRead,
)
from app.services.orchestration_service import OrchestrationService
from app.services.serializers import (
    project_to_read,
    project_to_summary,
    run_to_read,
)


class ProjectNotFound(Exception):
    pass


class RunNotFound(Exception):
    pass


class ProjectService:
    def __init__(self, session: AsyncSession, orchestrator: OrchestrationService) -> None:
        self._s = session
        self._orchestrator = orchestrator
        self._projects = ProjectRepository(session)
        self._runs = RunRepository(session)

    # --- Commands --------------------------------------------------------- #

    async def create_and_run(self, req: CreateProjectRequest) -> RunDetail:
        provider = req.provider or settings.llm_provider
        model = req.model or settings.default_model_for(provider)
        max_iterations = req.max_iterations or settings.max_iterations
        name = req.name or str(derive(req.idea, None)["product_name"])

        project = await self._projects.create(name=name, idea=req.idea, constraints=req.constraints)
        run = await self._runs.create(
            project_id=project.id,
            provider=provider,
            model=model,
            max_iterations=max_iterations,
        )
        await self._s.commit()

        self._orchestrator.launch(
            run_id=run.id,
            idea=req.idea,
            name=name,
            constraints=req.constraints,
            provider=provider,
            model=model,
            max_iterations=max_iterations,
        )
        return await self.get_run_detail(run.id)

    async def rerun(self, project_id: str) -> RunDetail:
        """Start a fresh run for an existing project (edit-and-rerun / retry)."""
        project = await self._projects.get(project_id)
        if project is None:
            raise ProjectNotFound(project_id)

        provider = settings.llm_provider
        model = settings.default_model_for(provider)
        run = await self._runs.create(
            project_id=project.id,
            provider=provider,
            model=model,
            max_iterations=settings.max_iterations,
        )
        await self._s.commit()

        self._orchestrator.launch(
            run_id=run.id,
            idea=project.idea,
            name=project.name,
            constraints=project.constraints,
            provider=provider,
            model=model,
            max_iterations=settings.max_iterations,
        )
        return await self.get_run_detail(run.id)

    # --- Queries ---------------------------------------------------------- #

    async def list_projects(self) -> list[ProjectSummary]:
        projects = await self._projects.list()
        return [project_to_summary(p) for p in projects]

    async def get_project(self, project_id: str) -> ProjectRead:
        project = await self._projects.get(project_id)
        if project is None:
            raise ProjectNotFound(project_id)
        latest = project.runs[0] if project.runs else None
        latest_read: RunRead | None = None
        if latest is not None:
            events = await self._runs.list_events(latest.id)
            latest_read = run_to_read(latest, events)
        return project_to_read(project, latest_read)

    async def get_run_detail(self, run_id: str) -> RunDetail:
        run = await self._runs.get(run_id)
        if run is None:
            raise RunNotFound(run_id)
        events = await self._runs.list_events(run_id)
        project = await self._projects.get(run.project_id)
        if project is None:
            raise ProjectNotFound(run.project_id)

        run_read = run_to_read(run, events)
        return RunDetail(
            run=run_read,
            project=project_to_read(project, run_read),
            outputs=run.outputs or {},
            events=[_event_to_dict(e) for e in events],
            artifact_count=len(run.artifacts),
        )


def _event_to_dict(event) -> dict:  # noqa: ANN001 - ORM RunEvent
    from app.schemas.enums import AgentRole

    agent = AgentRole(event.agent) if event.agent else None
    return {
        "id": event.id,
        "seq": event.seq,
        "run_id": event.run_id,
        "type": event.type,
        "agent": event.agent,
        "agent_label": agent.label if agent else None,
        "message": event.message,
        "iteration": event.iteration,
        "data": event.data,
        "created_at": event.created_at.isoformat(),
    }
