"""OpenAI-backed provider using LangChain's structured output."""

from __future__ import annotations

from app.llm.base import LLMProvider, T


class OpenAIProvider(LLMProvider):
    """Uses ``ChatOpenAI`` with ``with_structured_output`` for typed results."""

    name = "openai"

    def __init__(self, api_key: str, model: str, temperature: float = 0.4) -> None:
        from langchain_openai import ChatOpenAI

        self.model = model
        self._client = ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=temperature,
        )

    async def generate(self, *, system: str, prompt: str, schema: type[T], context: dict) -> T:
        structured = self._client.with_structured_output(schema)
        messages = [
            ("system", system),
            ("human", prompt),
        ]
        result = await structured.ainvoke(messages)
        return result  # type: ignore[return-value]

    async def generate_text(self, *, system: str, prompt: str, context: dict | None = None) -> str:
        messages = [
            ("system", system),
            ("human", prompt),
        ]
        result = await self._client.ainvoke(messages)
        return str(result.content) if result.content is not None else ""
