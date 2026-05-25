"""Product Manager agent — turns an idea into product definition."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.schemas.agent_io import ProductManagerOutput
from app.schemas.artifact import ArtifactBase
from app.schemas.enums import AgentRole, ArtifactKind


class ProductManagerAgent(BaseAgent):
    role = AgentRole.PRODUCT_MANAGER
    output_schema = ProductManagerOutput

    system_prompt = (
        "You are a senior Product Manager at an AI startup. You translate raw "
        "ideas into crisp product definitions: vision, target users, prioritized "
        "user stories, a tight MVP scope, explicit assumptions and risks, success "
        "metrics, and technical requirements. You are decisive and ruthless about "
        "scope. Always return structured data only."
    )

    def build_prompt(self, ctx: dict) -> str:
        constraints = ctx.get("constraints") or "None specified."
        return (
            f"Product idea:\n{ctx['idea']}\n\n"
            f"Constraints:\n{constraints}\n\n"
            "Define the product. Keep the MVP scope to the smallest set of "
            "features that validates the core value. Be explicit about what is "
            "out of scope and why."
        )

    def progress_steps(self, ctx: dict) -> list[str]:
        return [
            "Clarifying the core problem...",
            "Identifying target users...",
            "Drafting user stories and MVP scope...",
            "Surfacing assumptions and risks...",
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
        md = (
            f"# Product Definition\n\n"
            f"## Vision\n{output.product_vision}\n\n"
            f"## Target Users\n{self._bullets(output.target_users)}\n\n"
            f"## User Stories\n{stories}\n\n"
            f"## MVP Scope\n{self._bullets(output.mvp_scope)}\n\n"
            f"## Out of Scope\n{self._bullets(output.out_of_scope)}\n\n"
            f"## Assumptions\n{self._bullets(output.assumptions)}\n\n"
            f"## Risks\n{risks}\n\n"
            f"## Success Metrics\n{self._bullets(output.success_metrics)}\n\n"
            f"## Technical Requirements\n{self._bullets(output.technical_requirements)}\n"
        )
        return [
            ArtifactBase(
                title="Product Definition",
                path="docs/01-product-definition.md",
                kind=ArtifactKind.DOCUMENT,
                produced_by=self.role,
                content=md,
                summary=output.product_vision[:160],
            )
        ]
