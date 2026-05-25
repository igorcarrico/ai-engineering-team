"""Provider factory — resolves a provider name + model into a concrete client.

Falls back to the mock provider (with a warning) when a real provider is
requested without credentials, so a misconfigured demo degrades gracefully
instead of crashing.
"""

from __future__ import annotations

from app.config import ProviderName, settings
from app.llm.base import LLMProvider
from app.llm.mock_provider import MockProvider
from app.logging_config import get_logger

log = get_logger(__name__)


def build_provider(
    provider: ProviderName | None = None,
    model: str | None = None,
) -> LLMProvider:
    """Build an :class:`LLMProvider` for the requested provider/model."""
    provider = provider or settings.llm_provider
    model = model or settings.default_model_for(provider)

    if provider == "mock":
        return MockProvider(model="mock-architect-1", latency_seconds=settings.mock_latency_seconds)

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            log.warning("anthropic_requested_without_key", action="falling_back_to_mock")
            return MockProvider(latency_seconds=settings.mock_latency_seconds)
        from app.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(api_key=settings.anthropic_api_key, model=model)

    if provider == "openai":
        if not settings.openai_api_key:
            log.warning("openai_requested_without_key", action="falling_back_to_mock")
            return MockProvider(latency_seconds=settings.mock_latency_seconds)
        from app.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(api_key=settings.openai_api_key, model=model)

    raise ValueError(f"Unknown provider: {provider}")
