"""API DTOs for projects and runs (requests + responses)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.config import ProviderName
from app.schemas.enums import RunStatus, StepStatus

# --------------------------------------------------------------------------- #
# Requests
# --------------------------------------------------------------------------- #


class CreateProjectRequest(BaseModel):
    idea: str = Field(min_length=8, max_length=4000, description="The software idea in natural language")
    name: str | None = Field(default=None, max_length=160)
    constraints: str = Field(default="", max_length=2000)
    provider: ProviderName | None = None
    model: str | None = None
    max_iterations: int | None = Field(default=None, ge=1, le=5)


class RetryStepRequest(BaseModel):
    agent: str = Field(description="Agent key to re-run, e.g. 'architect'")


# --------------------------------------------------------------------------- #
# Responses
# --------------------------------------------------------------------------- #


class StepRead(BaseModel):
    agent: str
    label: str
    status: StepStatus
    iteration: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    retries: int = 0
    error: str | None = None


class RunRead(BaseModel):
    id: str
    project_id: str
    status: RunStatus
    provider: str
    model: str
    iteration: int
    max_iterations: int
    created_at: datetime
    updated_at: datetime
    duration_ms: int | None = None
    steps: list[StepRead] = Field(default_factory=list)
    review_score: int | None = None
    final_summary: str | None = None

    model_config = {"from_attributes": True}


class ProjectRead(BaseModel):
    id: str
    name: str
    idea: str
    constraints: str
    created_at: datetime
    updated_at: datetime
    latest_run: RunRead | None = None

    model_config = {"from_attributes": True}


class ProjectSummary(BaseModel):
    id: str
    name: str
    idea: str
    created_at: datetime
    latest_run_id: str | None = None
    latest_status: RunStatus | None = None
    review_score: int | None = None
    artifact_count: int = 0


class RunDetail(BaseModel):
    """Everything the dashboard needs to render a run in one payload."""

    run: RunRead
    project: ProjectRead
    outputs: dict[str, Any] = Field(default_factory=dict)
    events: list[dict[str, Any]] = Field(default_factory=list)
    artifact_count: int = 0
