"""FastAPI application factory.

Wires configuration, logging, persistence and the orchestrator together. The
orchestrator (which compiles the LangGraph workflow once) lives on
``app.state`` for the process lifetime.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import artifacts, chat, health, projects, runs
from app.config import settings
from app.core.events import hub
from app.db.session import init_db
from app.logging_config import configure_logging, get_logger
from app.services.orchestration_service import OrchestrationService

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await init_db()
    app.state.orchestrator = OrchestrationService(hub)
    log.info("app_started", version=__version__, provider=settings.llm_provider)
    yield
    log.info("app_stopping")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Engineering Team API",
        version=__version__,
        description=(
            "Backend for an autonomous multi-agent software engineering platform "
            "built on LangGraph. A team of specialized agents turns a software "
            "idea into a structured engineering plan and artifacts."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api_prefix = "/api"
    app.include_router(health.router, prefix=api_prefix)
    app.include_router(projects.router, prefix=api_prefix)
    app.include_router(runs.router, prefix=api_prefix)
    app.include_router(artifacts.router, prefix=api_prefix)
    app.include_router(chat.router, prefix=api_prefix)

    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        return {
            "name": "AI Engineering Team API",
            "version": __version__,
            "docs": "/docs",
            "health": "/api/health",
        }

    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.app_env == "development",
    )


if __name__ == "__main__":
    main()
