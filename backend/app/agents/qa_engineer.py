"""QA Engineer agent — defines test strategy, scenarios and gaps."""

from __future__ import annotations

import json

from app.agents.base import BaseAgent
from app.schemas.agent_io import QAOutput
from app.schemas.artifact import ArtifactBase
from app.schemas.enums import AgentRole, ArtifactKind

_UPSTREAM = [
    ("product_manager", "Product Manager"),
    ("architect", "Software Architect"),
    ("backend_engineer", "Backend Engineer"),
    ("frontend_engineer", "Frontend Engineer"),
]


class QAEngineerAgent(BaseAgent):
    role = AgentRole.QA_ENGINEER
    output_schema = QAOutput

    system_prompt = (
        "You are a meticulous QA Engineer. Given the product, architecture and "
        "engineering plans, you define a pragmatic test strategy, concrete test "
        "scenarios, edge cases, a QA checklist, and you flag missing requirements "
        "and risk areas. Always return structured data only."
    )

    def build_prompt(self, ctx: dict) -> str:
        sections = []
        for key, label in _UPSTREAM:
            out = ctx.get(key)
            if out:
                sections.append(f"### {label}\n```json\n{json.dumps(out, indent=2)}\n```")
        outputs_block = "\n\n".join(sections) if sections else "_No upstream outputs available._"
        return (
            f"Product idea:\n{ctx['idea']}\n\n"
            "Using the upstream team outputs below, define a test strategy, "
            "concrete test scenarios, edge cases, a QA checklist, and call out "
            "missing requirements and risk areas. Tie every item back to "
            "specific endpoints, components, user stories or risks from those "
            "outputs — do not be generic.\n\n"
            f"## Upstream outputs\n\n{outputs_block}"
        )

    def progress_steps(self, ctx: dict) -> list[str]:
        return [
            "Reviewing the engineering plans...",
            "Enumerating edge cases...",
            "Designing test scenarios...",
            "Compiling the QA checklist...",
        ]

    def build_artifacts(self, output: QAOutput, ctx: dict) -> list[ArtifactBase]:  # type: ignore[override]
        scenarios = "\n".join(
            f"### {s.title} _({s.type})_\n- Steps: {' → '.join(s.steps)}\n- Expected: {s.expected}"
            for s in output.test_scenarios
        )
        checklist = "\n".join(f"- [ ] **[{c.category}]** {c.item}" for c in output.qa_checklist)
        md = (
            f"# QA Plan\n\n"
            f"## Strategy\n{output.test_strategy}\n\n"
            f"## Test Scenarios\n{scenarios}\n\n"
            f"## Edge Cases\n{self._bullets(output.edge_cases)}\n\n"
            f"## Missing Requirements\n{self._bullets(output.missing_requirements)}\n\n"
            f"## Risk Areas\n{self._bullets(output.risk_areas)}\n\n"
            f"## QA Checklist\n{checklist}\n"
        )
        return [
            ArtifactBase(
                title="QA Plan",
                path="docs/05-qa-plan.md",
                kind=ArtifactKind.REPORT,
                produced_by=self.role,
                content=md,
                summary=f"{len(output.test_scenarios)} scenarios, {len(output.qa_checklist)} checks",
            )
        ]
