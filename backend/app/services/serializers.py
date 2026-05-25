"""Map ORM rows to API DTOs.

The agent *timeline* (steps) is derived from the persisted event log rather than
stored separately — the events are the single source of truth, so the timeline
can never drift from what actually happened.
"""

from __future__ import annotations

from app.agents.registry import AGENT_SEQUENCE
from app.models.db import Artifact, Project, Run, RunEvent
from app.schemas.artifact import ArtifactRead
from app.schemas.enums import AgentRole, EventType, RunStatus, StepStatus
from app.schemas.run import ProjectRead, ProjectSummary, RunRead, StepRead


def derive_steps(events: list[RunEvent]) -> list[StepRead]:
    """Reconstruct per-agent step status/timing from the event log."""
    by_agent: dict[str, list[RunEvent]] = {}
    for ev in events:
        if ev.agent:
            by_agent.setdefault(ev.agent, []).append(ev)

    steps: list[StepRead] = []
    for key in AGENT_SEQUENCE:
        evs = sorted(by_agent.get(key, []), key=lambda e: e.seq)
        label = AgentRole(key).label
        if not evs:
            steps.append(StepRead(agent=key, label=label, status=StepStatus.PENDING))
            continue

        started = [e for e in evs if e.type == EventType.AGENT_STARTED.value]
        completed = [e for e in evs if e.type == EventType.AGENT_COMPLETED.value]
        failed = [e for e in evs if e.type == EventType.AGENT_FAILED.value]
        retries = len([e for e in evs if e.type == EventType.AGENT_RETRY.value])
        iteration = max((e.iteration for e in evs), default=0)

        if failed and (not completed or failed[-1].seq > completed[-1].seq):
            status = StepStatus.FAILED
        elif completed:
            status = StepStatus.COMPLETED
        else:
            status = StepStatus.RUNNING

        started_at = started[-1].created_at if started else None
        finished_at = completed[-1].created_at if completed else None
        duration_ms = completed[-1].data.get("duration_ms") if completed else None
        error = failed[-1].data.get("error") if status is StepStatus.FAILED and failed else None

        steps.append(
            StepRead(
                agent=key,
                label=label,
                status=status,
                iteration=iteration,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                retries=retries,
                error=error,
            )
        )
    return steps


def run_to_read(run: Run, events: list[RunEvent]) -> RunRead:
    return RunRead(
        id=run.id,
        project_id=run.project_id,
        status=RunStatus(run.status),
        provider=run.provider,
        model=run.model,
        iteration=run.iteration,
        max_iterations=run.max_iterations,
        created_at=run.created_at,
        updated_at=run.updated_at,
        duration_ms=run.duration_ms,
        steps=derive_steps(events),
        review_score=run.review_score,
        final_summary=run.final_summary,
    )


def project_to_read(project: Project, latest_run: RunRead | None) -> ProjectRead:
    return ProjectRead(
        id=project.id,
        name=project.name,
        idea=project.idea,
        constraints=project.constraints,
        created_at=project.created_at,
        updated_at=project.updated_at,
        latest_run=latest_run,
    )


def project_to_summary(project: Project) -> ProjectSummary:
    latest = project.runs[0] if project.runs else None
    return ProjectSummary(
        id=project.id,
        name=project.name,
        idea=project.idea,
        created_at=project.created_at,
        latest_run_id=latest.id if latest else None,
        latest_status=RunStatus(latest.status) if latest else None,
        review_score=latest.review_score if latest else None,
        artifact_count=len(latest.artifacts) if latest else 0,
    )


def artifact_to_read(artifact: Artifact) -> ArtifactRead:
    return ArtifactRead.model_validate(artifact)
