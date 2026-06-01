"""FastAPI dependency providers."""

from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.llm.factory import build_provider
from app.services.artifact_service import ArtifactService
from app.services.brief_service import BriefService
from app.services.chat_service import ChatService
from app.services.orchestration_service import OrchestrationService
from app.services.project_service import ProjectService


def get_orchestrator(request: Request) -> OrchestrationService:
    """The process-wide orchestrator, created during app startup."""
    return request.app.state.orchestrator


def get_project_service(
    session: AsyncSession = Depends(get_session),
    orchestrator: OrchestrationService = Depends(get_orchestrator),
) -> ProjectService:
    return ProjectService(session, orchestrator)


def get_artifact_service(
    session: AsyncSession = Depends(get_session),
) -> ArtifactService:
    return ArtifactService(session)


def get_brief_service(
    session: AsyncSession = Depends(get_session),
) -> BriefService:
    return BriefService(session)


def get_chat_service(
    session: AsyncSession = Depends(get_session),
) -> ChatService:
    """Builds a fresh provider per request — config can change without restart."""
    return ChatService(session, provider=build_provider())
