"""Verdict Synthesizer — the founder-facing GO/NO-GO with budget and timeline.

Wears two hats:
- INTERNAL: engineering reviewer that drives the refine loop (verdict/score).
- EXTERNAL: lead consultant delivering the founder's decision card
  (go_no_go, timeline, budget, recommended team, kill criteria).
"""

from __future__ import annotations

import json

from app.agents.base import BaseAgent
from app.schemas.agent_io import CodeReviewOutput
from app.schemas.artifact import ArtifactBase
from app.schemas.enums import AgentRole, ArtifactKind

_PRIOR_AGENTS = [
    ("product_manager", "Product Strategist"),
    ("architect", "Solutions Architect"),
    ("backend_engineer", "Backend Estimator"),
    ("frontend_engineer", "Frontend Estimator"),
    ("qa_engineer", "Quality Risk Assessor"),
    ("security_reviewer", "Compliance & Legal Advisor"),
]


class CodeReviewerAgent(BaseAgent):
    role = AgentRole.CODE_REVIEWER
    output_schema = CodeReviewOutput

    system_prompt = (
        "You are the lead consultant on a feasibility-study team delivering the "
        "verdict to a non-technical founder. The team has analyzed the idea — you "
        "synthesize their work into a clear executive decision card.\n\n"
        "You wear two hats:\n"
        " 1. INTERNAL engineering review: score the plan 0-100, list strengths and "
        "issues, decide APPROVE or REVISE. If REVISE, give a precise "
        "revision_focus so the team's next pass is targeted.\n"
        " 2. FOUNDER-FACING verdict: a clear go_no_go (GO | GO_WITH_CONDITIONS | "
        "NO_GO) with concrete ranges:\n"
        "    - mvp_timeline and mvp_budget_usd_range\n"
        "    - v1_timeline and v1_budget_usd_range\n"
        "    - recommended_team (skill levels + headcount)\n"
        "    - top_questions_to_validate_first — the 3-5 questions the founder "
        "should answer BEFORE committing budget (discovery interviews, "
        "prototypes, market signals)\n"
        "    - kill_criteria — conditions under which to abandon the idea\n\n"
        "Founder is paying you for clarity, not for hedging. Specific numbers > "
        "vague ranges. If complexity is high and value is unproven, recommend "
        "GO_WITH_CONDITIONS and list what to validate first. If risks dominate, "
        "NO_GO honestly. Always return structured data only."
    )

    def build_prompt(self, ctx: dict) -> str:
        sections = []
        for key, label in _PRIOR_AGENTS:
            out = ctx.get(key)
            if out:
                sections.append(f"### {label}\n```json\n{json.dumps(out, indent=2)}\n```")
        outputs_block = "\n\n".join(sections) if sections else "_No prior outputs available._"
        return (
            f"## Founder's idea\n{ctx['idea']}\n\n"
            f"Iteration: {ctx.get('iteration', 0)}\n\n"
            "Synthesize the team's work below into a feasibility verdict.\n\n"
            "Lead with the FOUNDER-FACING fields (go_no_go, timelines, budget ranges, "
            "recommended_team, top_questions_to_validate_first, kill_criteria). "
            "These are read first.\n\n"
            "Then complete the INTERNAL engineering review (verdict APPROVE/REVISE, "
            "score 0-100, strengths, issues, consistency_checks). If you REVISE, "
            "give a precise revision_focus tied to specific gaps in the team's "
            "outputs.\n\n"
            "Reference the actual content of the outputs — do not be generic. "
            "Specific numbers and named risks beat vague language.\n\n"
            f"## Team outputs\n\n{outputs_block}"
        )

    def progress_steps(self, ctx: dict) -> list[str]:
        return [
            "Synthesizing the team's verdict...",
            "Estimating timeline and budget ranges...",
            "Identifying what to validate first...",
            "Writing the executive decision card...",
        ]

    def build_artifacts(self, output: CodeReviewOutput, ctx: dict) -> list[ArtifactBase]:  # type: ignore[override]
        issues = (
            "\n".join(
                f"- **[{i.severity.value.upper()}]** ({i.area}) {i.title}\n  - _Fix:_ {i.recommendation}"
                for i in output.issues
            )
            or "_None._"
        )

        founder_card = ""
        if output.go_no_go:
            founder_card += f"## Verdict\n# `{output.go_no_go.upper()}`\n\n"
        if output.verdict_rationale:
            founder_card += f"{output.verdict_rationale}\n\n"

        cost_table = []
        if output.mvp_timeline or output.mvp_budget_usd_range:
            cost_table.append(f"| **MVP** | {output.mvp_timeline or '—'} | {output.mvp_budget_usd_range or '—'} |")
        if output.v1_timeline or output.v1_budget_usd_range:
            cost_table.append(
                f"| **V1 (polished)** | {output.v1_timeline or '—'} | {output.v1_budget_usd_range or '—'} |"
            )
        if cost_table:
            founder_card += (
                "## Timeline & Budget\n\n"
                "| Stage | Timeline | Budget |\n|---|---|---|\n" + "\n".join(cost_table) + "\n\n"
            )

        if output.recommended_team:
            founder_card += f"## Recommended Team\n{output.recommended_team}\n\n"

        if output.top_questions_to_validate_first:
            founder_card += (
                f"## Validate Before Committing Budget\n{self._bullets(output.top_questions_to_validate_first)}\n\n"
            )

        if output.kill_criteria:
            founder_card += f"## Kill Criteria\n{self._bullets(output.kill_criteria)}\n\n"

        md = (
            f"# Go / No-Go Verdict\n\n"
            f"{founder_card}"
            f"---\n\n"
            f"## Engineering Review\n"
            f"**Plan quality:** `{output.verdict.value.upper()}` · "
            f"**Score:** {output.score}/100\n\n"
            f"### Assessment\n{output.overall_assessment}\n\n"
            f"### Strengths\n{self._bullets(output.strengths)}\n\n"
            f"### Issues\n{issues}\n\n"
            f"### Consistency Checks\n{self._bullets(output.consistency_checks)}\n"
        )
        if output.revision_focus:
            md += f"\n### Revision Focus (next iteration)\n{self._bullets(output.revision_focus)}\n"

        summary = (
            f"{output.go_no_go} · {output.mvp_timeline} · {output.mvp_budget_usd_range}"
            if output.go_no_go
            else f"{output.verdict.value} · score {output.score}/100"
        )
        return [
            ArtifactBase(
                title="Go / No-Go Verdict",
                path="docs/07-code-review.md",
                kind=ArtifactKind.REPORT,
                produced_by=self.role,
                content=md,
                summary=summary[:160],
            )
        ]
