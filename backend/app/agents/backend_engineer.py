"""Backend Effort Estimator — translates architecture into honest effort ranges."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.schemas.agent_io import BackendEngineerOutput
from app.schemas.artifact import ArtifactBase
from app.schemas.enums import AgentRole, ArtifactKind


class BackendEngineerAgent(BaseAgent):
    role = AgentRole.BACKEND_ENGINEER
    output_schema = BackendEngineerOutput

    system_prompt = (
        "You are a senior Backend Engineer estimating effort for a feasibility study. "
        "Your audience is a non-technical founder making a real spending decision — "
        "over-promise here costs them real money.\n\n"
        "Your job:\n"
        " 1. Translate the architecture into a concrete effort range (weeks, not days; "
        "include integration and testing overhead, not just happy-path coding).\n"
        " 2. State the team needed by skill level (e.g. '1 senior backend' vs "
        "'1 mid-level engineer + occasional senior review').\n"
        " 3. Identify the service modules and 2-3 starter code files that show the "
        "architecture is actually feasible. Code is illustrative, not production.\n\n"
        "Be conservative: ranges should reflect realistic delivery, not best-case. "
        "Always return structured data only."
    )

    def build_prompt(self, ctx: dict) -> str:
        arch = ctx.get("architect", {})
        pm = ctx.get("product_manager", {})
        components = [c.get("name", "") for c in arch.get("components", [])]
        return (
            f"## Architecture summary\n"
            f"- Complexity: {arch.get('complexity_rating', 'unknown')}\n"
            f"- Style: {arch.get('architecture_style', 'n/a')}\n"
            f"- Components: {', '.join(components) or 'n/a'}\n\n"
            f"## MVP scope (from PM)\n{self._bullets(pm.get('mvp_scope', []))}\n\n"
            "Estimate the backend MVP honestly. Give:\n"
            " - effort_estimate as a range in weeks (e.g. '6-9 weeks')\n"
            " - team_needed (skill level + headcount)\n"
            " - the service modules and endpoints (no need to be exhaustive)\n"
            " - 1-2 starter code files just to show feasibility\n"
            "Be conservative — include integration, auth, testing, deployment, not "
            "just feature code."
        )

    def progress_steps(self, ctx: dict) -> list[str]:
        return [
            "Sizing the backend work...",
            "Estimating realistic effort range...",
            "Picking the team profile needed...",
            "Sketching service modules and starter code...",
        ]

    def build_artifacts(self, output: BackendEngineerOutput, ctx: dict) -> list[ArtifactBase]:  # type: ignore[override]
        modules = "\n".join(
            f"- **{m.name}** — {m.responsibility}"
            + (f"\n  - Functions: `{'`, `'.join(m.key_functions)}`" if m.key_functions else "")
            for m in output.service_modules
        )
        endpoints = "\n".join(f"- `{e.method} {e.path}` — {e.description}" for e in output.endpoints)

        header = ""
        if output.effort_estimate:
            header += f"## Effort\n**Estimate:** {output.effort_estimate}\n\n"
        if output.team_needed:
            header += f"**Team needed:** {output.team_needed}\n\n"

        md = (
            f"# Backend Effort Estimate\n\n"
            f"{header}"
            f"## Service Modules\n{modules or '_None._'}\n\n"
            f"## Endpoints\n{endpoints or '_None._'}\n\n"
            f"## Implementation Notes\n{self._bullets(output.implementation_notes)}\n"
        )
        artifacts: list[ArtifactBase] = [
            ArtifactBase(
                title="Backend Effort Estimate",
                path="docs/03-backend-plan.md",
                kind=ArtifactKind.PLAN,
                produced_by=self.role,
                content=md,
                summary=output.effort_estimate or f"{len(output.service_modules)} modules",
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
