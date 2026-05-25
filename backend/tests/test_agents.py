"""Each agent must produce a valid output and at least one artifact."""

from __future__ import annotations

import pytest
from app.agents.registry import AGENT_SEQUENCE, get_agent
from app.llm.mock_provider import MockProvider
from app.schemas.artifact import ArtifactBase


@pytest.mark.parametrize("agent_key", AGENT_SEQUENCE)
async def test_agent_produces_output_and_artifacts(agent_key):
    agent = get_agent(agent_key)
    provider = MockProvider(latency_seconds=0)
    ctx = {
        "idea": "Build a SaaS platform for AI-powered financial analytics",
        "name": None,
        "iteration": 1,
        "constraints": "",
        # prior outputs some agents read from:
        "product_manager": {"mvp_scope": ["x"], "technical_requirements": ["y"]},
        "architect": {"architecture_style": "modular monolith", "components": [], "api_endpoints": []},
    }
    output = await agent.invoke(provider, ctx)
    assert isinstance(output, agent.output_schema)

    artifacts = agent.build_artifacts(output, ctx)
    assert len(artifacts) >= 1
    assert all(isinstance(a, ArtifactBase) for a in artifacts)
    assert all(a.content.strip() for a in artifacts)
