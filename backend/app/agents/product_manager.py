"""Product Strategist agent — frames the idea for a founder's go/no-go decision."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.schemas.agent_io import ProductManagerOutput
from app.schemas.artifact import ArtifactBase
from app.schemas.enums import AgentRole, ArtifactKind


class ProductManagerAgent(BaseAgent):
    role = AgentRole.PRODUCT_MANAGER
    output_schema = ProductManagerOutput

    system_prompt = (
        "You are a Product Strategist on a feasibility-study team whose client is a "
        "non-technical founder. Your job is NOT to write a polished product spec — "
        "it is to help the founder decide whether this idea is worth building.\n\n"
        "Distill the idea into a sharp one-sentence value proposition, identify the "
        "smallest version that would validate the bet (MVP), name the real risks "
        "(market, competition, financial, regulatory, not just engineering), and "
        "define one north-star metric with a concrete target.\n\n"
        "Be honest: if the value proposition is fuzzy or the target user is unclear, "
        "say so directly in the assumptions and risks. The founder is paying you for "
        "clarity, not for cheerleading. Always return structured data only."
    )

    def build_prompt(self, ctx: dict) -> str:
        constraints = ctx.get("constraints") or "None specified."
        return (
            f"## The founder's idea\n{ctx['idea']}\n\n"
            f"## Constraints\n{constraints}\n\n"
            "Produce the product brief for a feasibility study. Lead with a sharp "
            "value proposition and one primary metric with a concrete target. Keep "
            "the MVP scope to the smallest set of features that would actually "
            "validate the bet in market — not a full product. Be explicit about "
            "what is OUT of scope and why. List the real risks (market, financial, "
            "regulatory), not just generic technical ones."
        )

    def progress_steps(self, ctx: dict) -> list[str]:
        return [
            "Sharpening the value proposition...",
            "Identifying the real target user...",
            "Defining the smallest validating MVP...",
            "Surfacing market and financial risks...",
        ]

    def build_artifacts(self, output: ProductManagerOutput, ctx: dict) -> list[ArtifactBase]:  # type: ignore[override]
        stories = "\n".join(
            f"- **[{s.priority.value}]** As a {s.as_a}, I want {s.i_want}, so that {s.so_that}."
            for s in output.user_stories
        )
        risks = "\n".join(
            f"- **{r.severity.value.upper()}** — {r.description}\n  - _Mitigation:_ {r.mitigation}"
            for r in output.risks
        )

        header = ""
        if output.value_proposition:
            header += f"## Value Proposition\n> {output.value_proposition}\n\n"
        if output.primary_metric_target:
            header += f"## Primary Metric\n**{output.primary_metric_target}**\n\n"

        md = (
            f"# Product & Market Brief\n\n"
            f"{header}"
            f"## Vision\n{output.product_vision}\n\n"
            f"## Target Users\n{self._bullets(output.target_users)}\n\n"
            f"## User Stories\n{stories or '_None._'}\n\n"
            f"## MVP Scope — the smallest version that validates the bet\n"
            f"{self._bullets(output.mvp_scope)}\n\n"
            f"## Out of Scope\n{self._bullets(output.out_of_scope)}\n\n"
            f"## Assumptions\n{self._bullets(output.assumptions)}\n\n"
            f"## Risks\n{risks or '_None._'}\n\n"
            f"## Success Metrics\n{self._bullets(output.success_metrics)}\n\n"
            f"## Technical Requirements\n{self._bullets(output.technical_requirements)}\n"
        )
        return [
            ArtifactBase(
                title="Product & Market Brief",
                path="docs/01-product-definition.md",
                kind=ArtifactKind.DOCUMENT,
                produced_by=self.role,
                content=md,
                summary=(output.value_proposition or output.product_vision)[:160],
            )
        ]
