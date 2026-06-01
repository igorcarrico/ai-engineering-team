"""Post-run chat: the founder converses with the team after the verdict.

The chat reuses the agents' personas. When the user picks no agent, the question
goes to the Lead Consultant (the synthesizer). Each reply is grounded in the
full team's outputs plus the last few chat turns, so follow-ups stay coherent
with the original verdict.

Scope decision (v1): the reply is plain text. The agent describes what would
change in the plan if applicable, but does NOT regenerate artifacts. A future
"apply this change" action can re-run the relevant agent and update the docs.
"""

from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.registry import AGENTS
from app.llm.base import LLMProvider
from app.repositories.chat_repo import ChatRepository
from app.repositories.project_repo import ProjectRepository
from app.repositories.run_repo import RunRepository
from app.schemas.chat import ChatExchange, ChatMessageRead
from app.schemas.enums import AgentRole

_HISTORY_TURNS = 6  # last N messages included as conversation context
_AGENT_OUTPUT_KEYS = (
    "product_manager",
    "architect",
    "backend_engineer",
    "frontend_engineer",
    "qa_engineer",
    "security_reviewer",
    "code_reviewer",
)


class RunNotReady(Exception):
    pass


class ChatService:
    def __init__(self, session: AsyncSession, provider: LLMProvider) -> None:
        self._s = session
        self._provider = provider
        self._chat = ChatRepository(session)
        self._runs = RunRepository(session)
        self._projects = ProjectRepository(session)

    # --- Queries ---------------------------------------------------------- #

    async def list_messages(self, run_id: str) -> list[ChatMessageRead]:
        rows = await self._chat.list(run_id)
        return [_to_read(r) for r in rows]

    # --- Commands --------------------------------------------------------- #

    async def respond(self, *, run_id: str, content: str, agent: AgentRole | None) -> ChatExchange:
        run = await self._runs.get(run_id)
        if run is None:
            raise RunNotReady("Run not found")
        outputs = run.outputs or {}
        if not outputs:
            raise RunNotReady("The team hasn't produced any outputs yet. Wait for the run to complete.")

        target = agent or AgentRole.CODE_REVIEWER  # None -> Lead Consultant
        history = await self._chat.list(run_id)
        project = await self._projects.get(run.project_id)
        idea = project.idea if project else "(idea not available)"

        # 1) Persist the user's message and commit so it survives even if the
        #    provider call later fails.
        user_row = await self._chat.add(run_id=run_id, role="user", content=content, agent=target.value)
        await self._s.commit()

        # 2) Build the prompt for the chosen agent and call the LLM.
        system, prompt = _build_chat_prompt(
            target=target,
            project_idea=idea,
            outputs=outputs,
            history=history,
            user_content=content,
        )
        reply_text = await self._provider.generate_text(
            system=system,
            prompt=prompt,
            context={"agent_label": target.label},
        )

        # 3) Persist the assistant reply.
        assistant_row = await self._chat.add(run_id=run_id, role="assistant", content=reply_text, agent=target.value)
        await self._s.commit()

        return ChatExchange(
            user=_to_read(user_row),
            assistant=_to_read(assistant_row),
        )


def _to_read(message) -> ChatMessageRead:  # noqa: ANN001 - ORM type
    agent = AgentRole(message.agent) if message.agent else None
    return ChatMessageRead(
        id=message.id,
        seq=message.seq,
        run_id=message.run_id,
        role=message.role,
        agent=agent,
        agent_label=agent.label if agent else None,
        content=message.content,
        created_at=message.created_at,
    )


def _build_chat_prompt(
    *,
    target: AgentRole,
    project_idea: str,
    outputs: dict,
    history: list,
    user_content: str,
) -> tuple[str, str]:
    """Compose the system + user prompts for the target agent's chat reply."""

    # Pull the agent's persona, then append chat-mode framing.
    agent_obj = AGENTS.get(target.value)
    persona = agent_obj.system_prompt if agent_obj else ("You are the lead consultant on the feasibility-study team.")
    system = (
        f"{persona}\n\n"
        "You are now in POST-VERDICT CHAT MODE. The team has already produced its "
        "feasibility study. The founder is asking you a follow-up question.\n\n"
        " - Reply conversationally — 1 to 4 short paragraphs.\n"
        " - Ground every claim in the team's prior outputs and the original idea.\n"
        " - If the answer would change the plan, describe the change clearly but "
        "do NOT regenerate documents. The founder will decide whether to apply it.\n"
        " - If you don't know, say so honestly and suggest what to validate.\n"
        " - Never invent data — quote what the team said where useful."
    )

    # Compose the user prompt: idea + outputs + chat history + new question.
    sections: list[str] = []
    sections.append(f"## The founder's original idea\n{project_idea}")

    # Compact JSON of every agent's output (full team is cheap context).
    outputs_block = []
    for key in _AGENT_OUTPUT_KEYS:
        if key in outputs and outputs[key]:
            outputs_block.append(f"### {AgentRole(key).label}\n```json\n{json.dumps(outputs[key], indent=2)}\n```")
    if outputs_block:
        sections.append("## Team's verdict and outputs\n\n" + "\n\n".join(outputs_block))

    if history:
        recent = history[-_HISTORY_TURNS:]
        hist_lines = []
        for m in recent:
            speaker = "Founder" if m.role == "user" else (AgentRole(m.agent).label if m.agent else "Agent")
            hist_lines.append(f"**{speaker}:** {m.content}")
        sections.append("## Recent conversation\n\n" + "\n\n".join(hist_lines))

    sections.append(f"## New question from the founder\n{user_content}")
    sections.append(f"## Your reply\nReply as the {target.label}, conversationally and grounded in the outputs above.")

    return system, "\n\n".join(sections)
