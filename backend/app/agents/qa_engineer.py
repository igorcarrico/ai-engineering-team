"""Quality Risk Assessor — identifies how this product would fail in market."""

from __future__ import annotations

import json

from app.agents.base import BaseAgent
from app.schemas.agent_io import QAOutput
from app.schemas.artifact import ArtifactBase
from app.schemas.enums import AgentRole, ArtifactKind

_UPSTREAM = [
    ("product_manager", "Product Strategist"),
    ("architect", "Solutions Architect"),
    ("backend_engineer", "Backend Estimator"),
    ("frontend_engineer", "Frontend Estimator"),
]


class QAEngineerAgent(BaseAgent):
    role = AgentRole.QA_ENGINEER
    output_schema = QAOutput

    system_prompt = (
        "You are a Quality Risk Assessor on a feasibility-study team. Your job is "
        "NOT to write a comprehensive test plan — it is to tell the founder how "
        "this product would fail in the market.\n\n"
        "Specifically:\n"
        " 1. Identify the top 3 failure modes — the realistic ways this dies "
        "(unclear UX, scaled performance, data quality, integration breaks, "
        "competitor parity, etc.). Not 'bugs in code' — product-level failures.\n"
        " 2. Define the quality floor — the absolute minimum bar before launch. "
        "Skipping these will burn users on day one.\n"
        " 3. Concrete test scenarios for the critical user journey only — depth "
        "over breadth.\n"
        " 4. Surface missing requirements the founder hasn't thought about yet "
        "(idempotency, data retention, rate limits, etc.).\n\n"
        "Always return structured data only."
    )

    def build_prompt(self, ctx: dict) -> str:
        sections = []
        for key, label in _UPSTREAM:
            out = ctx.get(key)
            if out:
                sections.append(f"### {label}\n```json\n{json.dumps(out, indent=2)}\n```")
        outputs_block = "\n\n".join(sections) if sections else "_No upstream outputs available._"
        return (
            f"## Founder's idea\n{ctx['idea']}\n\n"
            "Using the upstream outputs below, assess the quality risk for a "
            "non-technical founder. Lead with:\n"
            " - the top 3 ways this product fails in market (failure_modes)\n"
            " - the quality_floor (non-skippable items)\n"
            "Then provide focused test scenarios, edge cases, missing requirements "
            "and a QA checklist tied to specific endpoints/components from those "
            "outputs. Be specific — do not be generic.\n\n"
            f"## Upstream outputs\n\n{outputs_block}"
        )

    def progress_steps(self, ctx: dict) -> list[str]:
        return [
            "Modeling how this product fails in market...",
            "Setting the minimum quality floor...",
            "Designing critical-path test scenarios...",
            "Surfacing missing requirements...",
        ]

    def build_artifacts(self, output: QAOutput, ctx: dict) -> list[ArtifactBase]:  # type: ignore[override]
        scenarios = "\n".join(
            f"### {s.title} _({s.type})_\n- Steps: {' → '.join(s.steps)}\n- Expected: {s.expected}"
            for s in output.test_scenarios
        )
        checklist = "\n".join(f"- [ ] **[{c.category}]** {c.item}" for c in output.qa_checklist)

        header = ""
        if output.failure_modes:
            header += f"## Top Failure Modes\n{self._bullets(output.failure_modes)}\n\n"
        if output.quality_floor:
            header += f"## Quality Floor — non-skippable\n{self._bullets(output.quality_floor)}\n\n"

        md = (
            f"# Quality Risk Assessment\n\n"
            f"{header}"
            f"## Strategy\n{output.test_strategy}\n\n"
            f"## Test Scenarios\n{scenarios or '_None._'}\n\n"
            f"## Edge Cases\n{self._bullets(output.edge_cases)}\n\n"
            f"## Missing Requirements\n{self._bullets(output.missing_requirements)}\n\n"
            f"## Risk Areas\n{self._bullets(output.risk_areas)}\n\n"
            f"## QA Checklist\n{checklist or '_None._'}\n"
        )
        return [
            ArtifactBase(
                title="Quality Risk Assessment",
                path="docs/05-qa-plan.md",
                kind=ArtifactKind.REPORT,
                produced_by=self.role,
                content=md,
                summary=(
                    output.failure_modes[0] if output.failure_modes else f"{len(output.test_scenarios)} scenarios"
                )[:160],
            )
        ]
