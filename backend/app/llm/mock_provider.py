"""Deterministic mock provider — runs the whole platform without API keys."""

from __future__ import annotations

import asyncio

from pydantic import BaseModel

from app.llm.base import LLMProvider, T
from app.llm.mock_data import GENERATORS, derive


class MockProvider(LLMProvider):
    """Returns tailored, schema-correct outputs with realistic latency.

    Dispatch is by the requested schema's class name, which maps 1:1 to the
    agent generators in :mod:`app.llm.mock_data`.
    """

    name = "mock"

    def __init__(self, model: str = "mock-architect-1", latency_seconds: float = 0.6) -> None:
        self.model = model
        self._latency = max(0.0, latency_seconds)

    async def generate(self, *, system: str, prompt: str, schema: type[T], context: dict) -> T:
        if self._latency:
            await asyncio.sleep(self._latency)

        derived = context.get("_derived")
        if derived is None:
            derived = derive(context.get("idea", ""), context.get("name"))
            context = {**context, "_derived": derived}

        key = _SCHEMA_TO_KEY.get(schema.__name__)
        if key is None or key not in GENERATORS:
            raise ValueError(f"No mock generator for schema {schema.__name__}")

        result: BaseModel = GENERATORS[key](context)
        # Guarantee the declared return type even if a generator drifts.
        if not isinstance(result, schema):
            result = schema.model_validate(result.model_dump())
        return result  # type: ignore[return-value]


_SCHEMA_TO_KEY = {
    "ProductManagerOutput": "product_manager",
    "ArchitectOutput": "architect",
    "BackendEngineerOutput": "backend_engineer",
    "FrontendEngineerOutput": "frontend_engineer",
    "QAOutput": "qa_engineer",
    "SecurityOutput": "security_reviewer",
    "CodeReviewOutput": "code_reviewer",
}
