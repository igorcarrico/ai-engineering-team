"""Central registry mapping agent keys to singleton agent instances."""

from __future__ import annotations

from app.agents.architect import ArchitectAgent
from app.agents.backend_engineer import BackendEngineerAgent
from app.agents.base import BaseAgent
from app.agents.code_reviewer import CodeReviewerAgent
from app.agents.frontend_engineer import FrontendEngineerAgent
from app.agents.product_manager import ProductManagerAgent
from app.agents.qa_engineer import QAEngineerAgent
from app.agents.security_reviewer import SecurityReviewerAgent
from app.schemas.enums import AgentRole

AGENTS: dict[str, BaseAgent] = {
    AgentRole.PRODUCT_MANAGER.value: ProductManagerAgent(),
    AgentRole.ARCHITECT.value: ArchitectAgent(),
    AgentRole.BACKEND_ENGINEER.value: BackendEngineerAgent(),
    AgentRole.FRONTEND_ENGINEER.value: FrontendEngineerAgent(),
    AgentRole.QA_ENGINEER.value: QAEngineerAgent(),
    AgentRole.SECURITY_REVIEWER.value: SecurityReviewerAgent(),
    AgentRole.CODE_REVIEWER.value: CodeReviewerAgent(),
}

# The order in which agents appear as steps in the UI timeline.
AGENT_SEQUENCE: list[str] = [
    AgentRole.PRODUCT_MANAGER.value,
    AgentRole.ARCHITECT.value,
    AgentRole.BACKEND_ENGINEER.value,
    AgentRole.FRONTEND_ENGINEER.value,
    AgentRole.QA_ENGINEER.value,
    AgentRole.SECURITY_REVIEWER.value,
    AgentRole.CODE_REVIEWER.value,
]


def get_agent(key: str) -> BaseAgent:
    if key not in AGENTS:
        raise KeyError(f"Unknown agent: {key}")
    return AGENTS[key]
