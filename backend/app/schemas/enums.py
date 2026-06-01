"""Shared enumerations used across schemas, the graph and the API."""

from __future__ import annotations

from enum import StrEnum


class AgentRole(StrEnum):
    """The specialized agents that make up the virtual engineering team."""

    PRODUCT_MANAGER = "product_manager"
    ARCHITECT = "architect"
    BACKEND_ENGINEER = "backend_engineer"
    FRONTEND_ENGINEER = "frontend_engineer"
    QA_ENGINEER = "qa_engineer"
    SECURITY_REVIEWER = "security_reviewer"
    CODE_REVIEWER = "code_reviewer"
    SUPERVISOR = "supervisor"

    @property
    def label(self) -> str:
        return {
            "product_manager": "Product Strategist",
            "architect": "Solutions Architect",
            "backend_engineer": "Backend Estimator",
            "frontend_engineer": "Frontend Estimator",
            "qa_engineer": "Quality Risk Assessor",
            "security_reviewer": "Compliance Advisor",
            "code_reviewer": "Lead Consultant",
            "supervisor": "Supervisor",
        }[self.value]


class RunStatus(StrEnum):
    """Lifecycle of a single workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(StrEnum):
    """Lifecycle of a single agent step within a run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class EventType(StrEnum):
    """Types of events emitted on the live activity stream."""

    RUN_STARTED = "run_started"
    AGENT_STARTED = "agent_started"
    AGENT_PROGRESS = "agent_progress"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    AGENT_RETRY = "agent_retry"
    ARTIFACT_CREATED = "artifact_created"
    ROUTING_DECISION = "routing_decision"
    ITERATION_STARTED = "iteration_started"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReviewVerdict(StrEnum):
    APPROVE = "approve"
    REVISE = "revise"


class ArtifactKind(StrEnum):
    DOCUMENT = "document"
    CODE = "code"
    DIAGRAM = "diagram"
    PLAN = "plan"
    REPORT = "report"
