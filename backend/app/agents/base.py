"""Base class shared by every agent.

An agent encapsulates *domain* behavior: who it is (system prompt), what task it
performs (prompt builder), and how it turns a typed result into artifacts. The
orchestration concerns — retries, timing, event emission — live in the graph
node wrapper, keeping agents small and testable.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field

from pydantic import BaseModel

from app.llm.base import LLMProvider
from app.schemas.artifact import ArtifactBase
from app.schemas.enums import AgentRole


@dataclass
class AgentResult:
    """What an agent produces in a single invocation."""

    role: AgentRole
    output: BaseModel
    artifacts: list[ArtifactBase] = field(default_factory=list)


class BaseAgent(abc.ABC):
    """Abstract specialized agent."""

    role: AgentRole
    output_schema: type[BaseModel]

    @property
    def title(self) -> str:
        return self.role.label

    # --- Prompting -------------------------------------------------------- #

    @property
    @abc.abstractmethod
    def system_prompt(self) -> str:
        """The agent's persona and operating instructions."""

    @abc.abstractmethod
    def build_prompt(self, ctx: dict) -> str:
        """Construct the task prompt from the current run context."""

    def progress_steps(self, ctx: dict) -> list[str]:
        """Short human-readable steps streamed to the activity feed."""
        return ["Analyzing inputs...", "Drafting output...", "Finalizing..."]

    # --- Artifacts -------------------------------------------------------- #

    @abc.abstractmethod
    def build_artifacts(self, output: BaseModel, ctx: dict) -> list[ArtifactBase]:
        """Render the structured output into workspace artifacts."""

    # --- Execution -------------------------------------------------------- #

    async def invoke(self, provider: LLMProvider, ctx: dict) -> BaseModel:
        """Call the provider to produce this agent's typed output."""
        return await provider.generate(
            system=self.system_prompt,
            prompt=self.build_prompt(ctx),
            schema=self.output_schema,
            context=ctx,
        )

    # --- Helpers ---------------------------------------------------------- #

    @staticmethod
    def _bullets(items: list[str]) -> str:
        return "\n".join(f"- {i}" for i in items)
