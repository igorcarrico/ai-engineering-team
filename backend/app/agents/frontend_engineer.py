"""Frontend Effort Estimator — sizes the UI work for the founder's budget."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.schemas.agent_io import FrontendEngineerOutput
from app.schemas.artifact import ArtifactBase
from app.schemas.enums import AgentRole, ArtifactKind


class FrontendEngineerAgent(BaseAgent):
    role = AgentRole.FRONTEND_ENGINEER
    output_schema = FrontendEngineerOutput

    system_prompt = (
        "You are a senior Frontend Engineer estimating UI effort for a feasibility "
        "study. Your audience is a non-technical founder.\n\n"
        "Your job:\n"
        " 1. Estimate the frontend MVP effort as a realistic range in weeks "
        "(include design + responsive + accessibility + browser testing, not "
        "just markup).\n"
        " 2. State the team needed (engineer skill + whether a designer is needed "
        "and at what %).\n"
        " 3. Identify the pages and key components — enough to size effort, not a "
        "full design spec.\n"
        " 4. 1-2 starter files just to show feasibility.\n\n"
        "Always insist on explicit loading, empty and error states in the plan. "
        "Always return structured data only."
    )

    def build_prompt(self, ctx: dict) -> str:
        pm = ctx.get("product_manager", {})
        arch = ctx.get("architect", {})
        return (
            f"## MVP scope (from PM)\n{self._bullets(pm.get('mvp_scope', []))}\n\n"
            f"## Complexity (from Architect)\n{arch.get('complexity_rating', 'unknown')}\n\n"
            "Estimate the frontend MVP honestly. Give:\n"
            " - effort_estimate as a range in weeks (include responsive + a11y + "
            "browser testing)\n"
            " - team_needed (engineer + designer % if needed)\n"
            " - the pages and key components\n"
            " - state management approach\n"
            " - 1-2 starter UI files to show feasibility (Next.js + TS + Tailwind)"
        )

    def progress_steps(self, ctx: dict) -> list[str]:
        return [
            "Sizing the frontend work...",
            "Estimating realistic effort range...",
            "Picking the team profile (engineer + designer?)...",
            "Sketching pages and components...",
        ]

    def build_artifacts(self, output: FrontendEngineerOutput, ctx: dict) -> list[ArtifactBase]:  # type: ignore[override]
        pages = "\n".join(f"- `{p.route}` — **{p.name}**: {p.description}" for p in output.pages)
        comps = "\n".join(
            f"- **{c.name}** — {c.description}" + (f" _(props: {', '.join(c.props)})_" if c.props else "")
            for c in output.components
        )

        header = ""
        if output.effort_estimate:
            header += f"## Effort\n**Estimate:** {output.effort_estimate}\n\n"
        if output.team_needed:
            header += f"**Team needed:** {output.team_needed}\n\n"

        md = (
            f"# Frontend Effort Estimate\n\n"
            f"{header}"
            f"## Pages\n{pages or '_None._'}\n\n"
            f"## Components\n{comps or '_None._'}\n\n"
            f"## State Management\n{output.state_management or '_Not specified._'}\n\n"
            f"## Implementation Notes\n{self._bullets(output.implementation_notes)}\n"
        )
        artifacts: list[ArtifactBase] = [
            ArtifactBase(
                title="Frontend Effort Estimate",
                path="docs/04-frontend-plan.md",
                kind=ArtifactKind.PLAN,
                produced_by=self.role,
                content=md,
                summary=output.effort_estimate or f"{len(output.pages)} pages",
            )
        ]
        for f in output.files:
            artifacts.append(
                ArtifactBase(
                    title=f.path.split("/")[-1],
                    path=f.path,
                    kind=ArtifactKind.CODE,
                    language=f.language,
                    produced_by=self.role,
                    content=f.content,
                    summary=f.description,
                )
            )
        return artifacts
