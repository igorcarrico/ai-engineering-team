"""Code Reviewer agent — reviews all outputs and decides approve/revise."""

from __future__ import annotations

import json

from app.agents.base import BaseAgent
from app.schemas.agent_io import CodeReviewOutput
from app.schemas.artifact import ArtifactBase
from app.schemas.enums import AgentRole, ArtifactKind

_PRIOR_AGENTS = [
    ("product_manager", "Product Manager"),
    ("architect", "Software Architect"),
    ("backend_engineer", "Backend Engineer"),
    ("frontend_engineer", "Frontend Engineer"),
    ("qa_engineer", "QA Engineer"),
    ("security_reviewer", "Security Reviewer"),
]


class CodeReviewerAgent(BaseAgent):
    role = AgentRole.CODE_REVIEWER
    output_schema = CodeReviewOutput

    system_prompt = (
        "You are a principal engineer performing a holistic review of the entire "
        "team's output. You check cross-agent consistency, engineering quality and "
        "architectural soundness, then decide: APPROVE if implementation-ready, or "
        "REVISE with a focused list of what the next iteration must fix. Be fair "
        "but exacting. Always return structured data only."
    )

    def build_prompt(self, ctx: dict) -> str:
        sections = []
        for key, label in _PRIOR_AGENTS:
            out = ctx.get(key)
            if out:
                sections.append(f"### {label}\n```json\n{json.dumps(out, indent=2)}\n```")
        outputs_block = "\n\n".join(sections) if sections else "_No prior outputs available._"
        return (
            f"Iteration: {ctx.get('iteration', 0)}\n\n"
            "Review the combined outputs of the team below. Score engineering "
            "quality 0-100, list concrete strengths and issues (each tied to a "
            "specific agent area), verify cross-agent consistency, and decide "
            "APPROVE or REVISE. If REVISE, provide a precise revision_focus "
            "list for the next iteration. Reference the actual content of the "
            "outputs — do not be generic.\n\n"
            f"## Team outputs\n\n{outputs_block}"
        )

    def progress_steps(self, ctx: dict) -> list[str]:
        return [
            "Cross-checking all agent outputs...",
            "Validating architectural consistency...",
            "Scoring engineering quality...",
            "Deciding verdict...",
        ]

    def build_artifacts(self, output: CodeReviewOutput, ctx: dict) -> list[ArtifactBase]:  # type: ignore[override]
        issues = (
            "\n".join(
                f"- **[{i.severity.value.upper()}]** ({i.area}) {i.title}\n  - _Fix:_ {i.recommendation}"
                for i in output.issues
            )
            or "_None._"
        )
        md = (
            f"# Code Review\n\n"
            f"**Verdict:** `{output.verdict.value.upper()}` · **Score:** {output.score}/100\n\n"
            f"## Assessment\n{output.overall_assessment}\n\n"
            f"## Strengths\n{self._bullets(output.strengths)}\n\n"
            f"## Issues\n{issues}\n\n"
            f"## Consistency Checks\n{self._bullets(output.consistency_checks)}\n"
        )
        if output.revision_focus:
            md += f"\n## Revision Focus (next iteration)\n{self._bullets(output.revision_focus)}\n"
        return [
            ArtifactBase(
                title="Code Review",
                path="docs/07-code-review.md",
                kind=ArtifactKind.REPORT,
                produced_by=self.role,
                content=md,
                summary=f"{output.verdict.value} · score {output.score}/100",
            )
        ]
