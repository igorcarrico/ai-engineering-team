"""Software Architect agent — designs the system."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.schemas.agent_io import ArchitectOutput
from app.schemas.artifact import ArtifactBase
from app.schemas.enums import AgentRole, ArtifactKind


class ArchitectAgent(BaseAgent):
    role = AgentRole.ARCHITECT
    output_schema = ArchitectOutput

    system_prompt = (
        "You are a pragmatic Staff Software Architect. Given a product definition, "
        "you design a system that is simple enough to ship and clean enough to "
        "scale: architecture style, components, data model, API surface, "
        "infrastructure and scalability strategy. You avoid over-engineering and "
        "justify trade-offs. Always return structured data only."
    )

    def build_prompt(self, ctx: dict) -> str:
        pm = ctx.get("product_manager", {})
        focus = ctx.get("revision_focus")
        revision = f"\n\nThis is a refinement pass. Address specifically:\n{self._bullets(focus)}" if focus else ""
        return (
            f"Product idea:\n{ctx['idea']}\n\n"
            f"MVP scope:\n{self._bullets(pm.get('mvp_scope', []))}\n\n"
            f"Technical requirements:\n{self._bullets(pm.get('technical_requirements', []))}\n\n"
            f"Design the architecture for the MVP.{revision}"
        )

    def progress_steps(self, ctx: dict) -> list[str]:
        return [
            "Selecting an architecture style...",
            "Defining components and boundaries...",
            "Designing the data model...",
            "Mapping the API surface...",
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
        md = (
            f"# System Architecture\n\n"
            f"## Overview\n{output.architecture_overview}\n\n"
            f"**Style:** {output.architecture_style}\n\n"
            f"## Components\n{components}\n\n"
            f"## Data Model\n{entities}\n\n"
            f"## API Surface\n\n| Method | Path | Description | Auth |\n|---|---|---|---|\n{endpoints}\n\n"
            f"## Tech Stack\n{stack}\n\n"
            f"## Infrastructure\n{self._bullets(output.infrastructure)}\n\n"
            f"## Scalability\n{self._bullets(output.scalability_notes)}\n"
        )
        diagram = self._mermaid(output)
        return [
            ArtifactBase(
                title="System Architecture",
                path="docs/02-architecture.md",
                kind=ArtifactKind.DOCUMENT,
                produced_by=self.role,
                content=md,
                summary=output.architecture_style,
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
