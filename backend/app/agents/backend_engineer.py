"""Backend Engineer agent — proposes backend structure and code artifacts."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.schemas.agent_io import BackendEngineerOutput
from app.schemas.artifact import ArtifactBase
from app.schemas.enums import AgentRole, ArtifactKind


class BackendEngineerAgent(BaseAgent):
    role = AgentRole.BACKEND_ENGINEER
    output_schema = BackendEngineerOutput

    system_prompt = (
        "You are a senior Backend Engineer. Given an architecture, you propose a "
        "concrete backend structure: service modules, endpoints, and starter file "
        "artifacts with realistic, idiomatic code. You favor dependency injection, "
        "async I/O and testability. Always return structured data only."
    )

    def build_prompt(self, ctx: dict) -> str:
        arch = ctx.get("architect", {})
        return (
            f"Architecture style: {arch.get('architecture_style', 'n/a')}\n\n"
            f"Components:\n{self._bullets([c.get('name', '') for c in arch.get('components', [])])}\n\n"
            "Propose the backend service modules, key endpoints, and 2-3 starter "
            "code files. Keep code idiomatic and production-leaning."
        )

    def progress_steps(self, ctx: dict) -> list[str]:
        return [
            "Mapping service modules...",
            "Designing the service layer...",
            "Generating starter code files...",
        ]

    def build_artifacts(self, output: BackendEngineerOutput, ctx: dict) -> list[ArtifactBase]:  # type: ignore[override]
        modules = "\n".join(
            f"- **{m.name}** — {m.responsibility}"
            + (f"\n  - Functions: `{'`, `'.join(m.key_functions)}`" if m.key_functions else "")
            for m in output.service_modules
        )
        endpoints = "\n".join(f"- `{e.method} {e.path}` — {e.description}" for e in output.endpoints)
        md = (
            f"# Backend Implementation Plan\n\n"
            f"## Service Modules\n{modules}\n\n"
            f"## Endpoints\n{endpoints}\n\n"
            f"## Implementation Notes\n{self._bullets(output.implementation_notes)}\n"
        )
        artifacts: list[ArtifactBase] = [
            ArtifactBase(
                title="Backend Plan",
                path="docs/03-backend-plan.md",
                kind=ArtifactKind.PLAN,
                produced_by=self.role,
                content=md,
                summary=f"{len(output.service_modules)} modules, {len(output.endpoints)} endpoints",
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
