"""Solutions Architect agent — translates the idea into engineering complexity."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.schemas.agent_io import ArchitectOutput
from app.schemas.artifact import ArtifactBase
from app.schemas.enums import AgentRole, ArtifactKind


class ArchitectAgent(BaseAgent):
    role = AgentRole.ARCHITECT
    output_schema = ArchitectOutput

    system_prompt = (
        "You are a Solutions Architect on a feasibility-study team. Your audience "
        "is a non-technical founder making an investment decision — not other "
        "engineers.\n\n"
        "Your job is NOT to design a perfect production system. It is to honestly "
        "assess how hard this is to build, so the founder can size effort and "
        "budget. Specifically:\n"
        " 1. Rate overall complexity (simple | moderate | complex | very_complex) "
        "and name the 2-4 concrete things that drive it (integrations, scale, "
        "novelty, regulation, data, ML, etc.).\n"
        " 2. For every major capability, recommend BUILD vs BUY. Favor existing "
        "SaaS/libraries unless there is a real reason to build custom. Name "
        "specific vendors when possible (Stripe, Auth0, SendGrid, etc.).\n"
        " 3. Sketch only enough architecture for engineers to estimate effort. "
        "Skip premature optimization.\n\n"
        "Always return structured data only."
    )

    def build_prompt(self, ctx: dict) -> str:
        pm = ctx.get("product_manager", {})
        focus = ctx.get("revision_focus")
        revision = f"\n\nThis is a refinement pass. Address specifically:\n{self._bullets(focus)}" if focus else ""
        return (
            f"## Founder's idea\n{ctx['idea']}\n\n"
            f"## MVP scope (from Product Strategist)\n{self._bullets(pm.get('mvp_scope', []))}\n\n"
            f"## Technical requirements\n{self._bullets(pm.get('technical_requirements', []))}\n\n"
            "Assess the engineering complexity for the MVP. Rate complexity with "
            "the drivers. Recommend build-vs-buy for every major capability "
            "(authentication, payments, search, AI/ML, hosting, monitoring, "
            "analytics, etc.). Sketch the minimum architecture needed for the "
            "engineers to estimate effort — no more."
            f"{revision}"
        )

    def progress_steps(self, ctx: dict) -> list[str]:
        return [
            "Rating overall complexity...",
            "Identifying the hard parts...",
            "Recommending build vs buy per capability...",
            "Sketching minimum architecture...",
        ]

    def build_artifacts(self, output: ArchitectOutput, ctx: dict) -> list[ArtifactBase]:  # type: ignore[override]
        components = "\n".join(f"- **{c.name}** ({c.technology}) — {c.responsibility}" for c in output.components)
        entities = "\n".join(
            f"### {e.name}\n- Fields: {', '.join(e.fields)}\n- Relationships: {', '.join(e.relationships) or '—'}"
            for e in output.data_model
        )
        endpoints = "\n".join(
            f"| `{ep.method}` | `{ep.path}` | {ep.description} | {'yes' if ep.auth_required else 'no'} |"
            for ep in output.api_endpoints
        )
        stack = "\n".join(f"- **{k}**: {v}" for k, v in output.tech_stack.items())
        bvb = "\n".join(
            f"- **{b.capability}** → `{b.recommendation.upper()}`"
            f"{' (' + b.suggested_vendor + ')' if b.suggested_vendor else ''}"
            f"\n  - _{b.why}_"
            for b in output.build_vs_buy
        )

        header = ""
        if output.complexity_rating:
            header += f"## Complexity\n**Rating:** `{output.complexity_rating.upper()}`\n\n"
        if output.complexity_drivers:
            header += f"**Drivers:**\n{self._bullets(output.complexity_drivers)}\n\n"
        if bvb:
            header += f"## Build vs Buy\n{bvb}\n\n"

        md = (
            f"# Solution Complexity Assessment\n\n"
            f"{header}"
            f"## Overview\n{output.architecture_overview}\n\n"
            f"**Style:** {output.architecture_style}\n\n"
            f"## Components\n{components or '_None._'}\n\n"
            f"## Data Model\n{entities or '_None._'}\n\n"
            f"## API Surface\n\n"
            f"| Method | Path | Description | Auth |\n|---|---|---|---|\n{endpoints or '| — | — | — | — |'}\n\n"
            f"## Tech Stack\n{stack or '_None._'}\n\n"
            f"## Infrastructure\n{self._bullets(output.infrastructure)}\n\n"
            f"## Scalability\n{self._bullets(output.scalability_notes)}\n"
        )
        diagram = self._mermaid(output)
        return [
            ArtifactBase(
                title="Solution Complexity Assessment",
                path="docs/02-architecture.md",
                kind=ArtifactKind.DOCUMENT,
                produced_by=self.role,
                content=md,
                summary=f"Complexity: {output.complexity_rating or output.architecture_style}",
            ),
            ArtifactBase(
                title="Architecture Diagram",
                path="docs/02-architecture-diagram.md",
                kind=ArtifactKind.DIAGRAM,
                language="mermaid",
                produced_by=self.role,
                content=diagram,
                summary="Component diagram (Mermaid)",
            ),
        ]

    @staticmethod
    def _mermaid(output: ArchitectOutput) -> str:
        lines = ["```mermaid", "flowchart TD", '    user(("User"))']
        for i, c in enumerate(output.components):
            lines.append(f'    c{i}["{c.name}<br/><small>{c.technology}</small>"]')
        if output.components:
            lines.append("    user --> c0")
            for i in range(len(output.components) - 1):
                lines.append(f"    c{i} --> c{i + 1}")
        lines.append("```")
        return "\n".join(lines)
