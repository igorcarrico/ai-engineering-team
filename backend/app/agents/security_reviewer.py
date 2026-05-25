"""Security Reviewer agent — identifies security and prompt-injection risks."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.schemas.agent_io import SecurityOutput
from app.schemas.artifact import ArtifactBase
from app.schemas.enums import AgentRole, ArtifactKind


class SecurityReviewerAgent(BaseAgent):
    role = AgentRole.SECURITY_REVIEWER
    output_schema = SecurityOutput

    system_prompt = (
        "You are an application Security Reviewer. You analyze the proposed system "
        "for authentication/authorization gaps, injection risks, data-protection "
        "issues, infrastructure exposure and — for AI systems — prompt-injection "
        "vectors. Each finding is actionable. Always return structured data only."
    )

    def build_prompt(self, ctx: dict) -> str:
        arch = ctx.get("architect", {})
        endpoints = [f"{e.get('method')} {e.get('path')}" for e in arch.get("api_endpoints", [])]
        return (
            f"System architecture style: {arch.get('architecture_style', 'n/a')}\n\n"
            f"API endpoints:\n{self._bullets(endpoints)}\n\n"
            "Identify security findings with severity and recommendations, list "
            "prompt-injection risks, auth recommendations and compliance notes."
        )

    def progress_steps(self, ctx: dict) -> list[str]:
        return [
            "Modeling the threat surface...",
            "Checking authN/authZ boundaries...",
            "Assessing prompt-injection vectors...",
            "Writing findings...",
        ]

    def build_artifacts(self, output: SecurityOutput, ctx: dict) -> list[ArtifactBase]:  # type: ignore[override]
        findings = "\n".join(
            f"### {f.title}\n- **Severity:** {f.severity.value.upper()} · **Category:** {f.category}\n"
            f"- {f.description}\n- _Recommendation:_ {f.recommendation}"
            for f in output.findings
        )
        md = (
            f"# Security Review\n\n"
            f"**Overall risk:** {output.overall_risk.value.upper()}\n\n"
            f"## Findings\n{findings}\n\n"
            f"## Prompt Injection Risks\n{self._bullets(output.prompt_injection_risks)}\n\n"
            f"## Auth Recommendations\n{self._bullets(output.auth_recommendations)}\n\n"
            f"## Compliance Notes\n{self._bullets(output.compliance_notes)}\n"
        )
        return [
            ArtifactBase(
                title="Security Review",
                path="docs/06-security-review.md",
                kind=ArtifactKind.REPORT,
                produced_by=self.role,
                content=md,
                summary=f"Overall risk: {output.overall_risk.value} · {len(output.findings)} findings",
            )
        ]
