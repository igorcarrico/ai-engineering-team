"""Anthropic-backed provider using LangChain's structured output."""

from __future__ import annotations

from app.llm.base import LLMProvider, T


class AnthropicProvider(LLMProvider):
    """Uses ``ChatAnthropic`` with ``with_structured_output`` for typed results.

    LangChain is used here precisely because it normalizes structured output and
    tool-calling across providers — exactly the "use LangChain where useful" case.
    """

    name = "anthropic"

    def __init__(self, api_key: str, model: str, temperature: float = 0.4) -> None:
        # Imported lazily so the package is only required when this provider is used.
        from langchain_anthropic import ChatAnthropic

        self.model = model
        self._client = ChatAnthropic(
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=4096,
        )

    async def generate(self, *, system: str, prompt: str, schema: type[T], context: dict) -> T:
        structured = self._client.with_structured_output(schema)
        messages = [
            ("system", system),
            ("human", prompt),
        ]
        result = await structured.ainvoke(messages)
        return result  # type: ignore[return-value]
