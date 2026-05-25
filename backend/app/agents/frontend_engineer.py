"""Frontend Engineer agent — proposes UI structure and code artifacts."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.schemas.agent_io import FrontendEngineerOutput
from app.schemas.artifact import ArtifactBase
from app.schemas.enums import AgentRole, ArtifactKind


class FrontendEngineerAgent(BaseAgent):
    role = AgentRole.FRONTEND_ENGINEER
    output_schema = FrontendEngineerOutput

    system_prompt = (
        "You are a senior Frontend Engineer specialized in Next.js + TypeScript. "
        "Given an architecture and product scope, you define pages, components, "
        "state management and starter UI code. You insist on explicit loading, "
        "empty and error states. Always return structured data only."
    )

    def build_prompt(self, ctx: dict) -> str:
        pm = ctx.get("product_manager", {})
        return (
            f"MVP scope:\n{self._bullets(pm.get('mvp_scope', []))}\n\n"
            "Define the frontend pages, key reusable components, the state "
            "management approach, and 1-2 starter UI files (Next.js + TS + Tailwind)."
        )

    def progress_steps(self, ctx: dict) -> list[str]:
        return [
            "Mapping pages and routes...",
            "Designing reusable components...",
            "Generating starter UI files...",
        ]

    def build_artifacts(self, output: FrontendEngineerOutput, ctx: dict) -> list[ArtifactBase]:  # type: ignore[override]
        pages = "\n".join(f"- `{p.route}` — **{p.name}**: {p.description}" for p in output.pages)
        comps = "\n".join(
            f"- **{c.name}** — {c.description}" + (f" _(props: {', '.join(c.props)})_" if c.props else "")
            for c in output.components
        )
        md = (
            f"# Frontend Implementation Plan\n\n"
            f"## Pages\n{pages}\n\n"
            f"## Components\n{comps}\n\n"
            f"## State Management\n{output.state_management}\n\n"
            f"## Implementation Notes\n{self._bullets(output.implementation_notes)}\n"
        )
        artifacts: list[ArtifactBase] = [
            ArtifactBase(
                title="Frontend Plan",
                path="docs/04-frontend-plan.md",
                kind=ArtifactKind.PLAN,
                produced_by=self.role,
                content=md,
                summary=f"{len(output.pages)} pages, {len(output.components)} components",
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
