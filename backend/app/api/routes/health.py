"""Health and runtime-configuration endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.config import settings

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "version": __version__,
        "provider": settings.llm_provider,
    }


@router.get("/config")
async def runtime_config() -> dict:
    """Non-secret runtime configuration the frontend can display."""
    return {
        "version": __version__,
        "default_provider": settings.llm_provider,
        "providers": ["mock", "anthropic", "openai"],
        "models": {
            "anthropic": settings.anthropic_model,
            "openai": settings.openai_model,
            "mock": "mock-architect-1",
        },
        "max_iterations": settings.max_iterations,
        "agents": [
            "product_manager",
            "architect",
            "backend_engineer",
            "frontend_engineer",
            "qa_engineer",
            "security_reviewer",
            "code_reviewer",
        ],
    }
