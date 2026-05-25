"""Provider-agnostic LLM interface.

Every agent depends on this small surface, never on a concrete SDK. That makes
the whole system testable (via the mock provider) and provider-portable
(Anthropic, OpenAI, or anything added later).
"""

from __future__ import annotations

import abc
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(abc.ABC):
    """Abstract base class for structured-output LLM providers."""

    #: Human-readable provider id ("mock", "anthropic", "openai").
    name: str = "base"
    #: The concrete model identifier in use.
    model: str = "unknown"

    @abc.abstractmethod
    async def generate(
        self,
        *,
        system: str,
        prompt: str,
        schema: type[T],
        context: dict,
    ) -> T:
        """Produce an instance of ``schema``.

        Args:
            system: The agent's system / role prompt.
            prompt: The task-specific user prompt.
            schema: The Pydantic model the result must conform to.
            context: Structured run context (idea, constraints, prior outputs).
                Real providers may ignore it; the mock provider uses it to craft
                tailored, deterministic results.
        """
        raise NotImplementedError

    def describe(self) -> dict[str, str]:
        return {"provider": self.name, "model": self.model}
