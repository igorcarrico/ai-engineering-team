"""The mock provider must satisfy every agent's output contract."""

from __future__ import annotations

import pytest
from app.llm.mock_provider import MockProvider
from app.schemas.agent_io import AGENT_OUTPUT_SCHEMAS


@pytest.mark.parametrize("key,schema", list(AGENT_OUTPUT_SCHEMAS.items()))
async def test_mock_provider_returns_valid_schema(key, schema):
    provider = MockProvider(latency_seconds=0)
    ctx = {"idea": "Build a SaaS for AI financial analytics", "name": None, "iteration": 1}
    result = await provider.generate(system="s", prompt="p", schema=schema, context=ctx)
    assert isinstance(result, schema)


async def test_mock_provider_is_deterministic():
    provider = MockProvider(latency_seconds=0)
    ctx = {"idea": "A note-taking app", "iteration": 0}
    from app.schemas.agent_io import ProductManagerOutput

    a = await provider.generate(system="", prompt="", schema=ProductManagerOutput, context=ctx)
    b = await provider.generate(system="", prompt="", schema=ProductManagerOutput, context=ctx)
    assert a.model_dump() == b.model_dump()
