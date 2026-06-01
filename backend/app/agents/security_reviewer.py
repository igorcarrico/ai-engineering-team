"""Compliance & Legal Advisor — surfaces regulatory blockers and lead times."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.schemas.agent_io import SecurityOutput
from app.schemas.artifact import ArtifactBase
from app.schemas.enums import AgentRole, ArtifactKind


class SecurityReviewerAgent(BaseAgent):
    role = AgentRole.SECURITY_REVIEWER
    output_schema = SecurityOutput

    system_prompt = (
        "You are a Compliance & Legal Advisor on a feasibility-study team. Your "
        "audience is a non-technical founder.\n\n"
        "Your job is NOT to do a security audit — it is to surface what the founder "
        "needs to plan for legally/regulatorily before they spend money building. "
        "Specifically:\n"
        " 1. List concrete compliance_requirements with the trigger (GDPR if EU "
        "users, LGPD if Brazil, PCI if cards, HIPAA if health data, financial "
        "licensing, age restrictions, etc.) and rough lead_time_weeks.\n"
        " 2. Flag whether a specialist (lawyer, DPO, security consultant) is "
        "required before launch — requires_specialist.\n"
        " 3. Surface legal_blockers — anything that could PREVENT launch in the "
        "target geography (data residency, banking license, content moderation).\n"
        " 4. Still produce technical findings, prompt-injection risks and auth "
        "recommendations for the team — but lead with what the founder needs to "
        "decide on first.\n\n"
        "Always return structured data only."
    )

    def build_prompt(self, ctx: dict) -> str:
        arch = ctx.get("architect", {})
        pm = ctx.get("product_manager", {})
        endpoints = [f"{e.get('method')} {e.get('path')}" for e in arch.get("api_endpoints", [])]
        return (
            f"## Founder's idea\n{ctx['idea']}\n\n"
            f"## Target users (from PM)\n{self._bullets(pm.get('target_users', []))}\n\n"
            f"## Architecture\n- Style: {arch.get('architecture_style', 'n/a')}\n"
            f"- Endpoints:\n{self._bullets(endpoints)}\n\n"
            "Lead with compliance/legal items the founder must plan for. Specifically:\n"
            " - compliance_requirements with triggers (EU users → GDPR, "
            "Brazil users → LGPD, cards → PCI, health → HIPAA, etc.) and lead times\n"
            " - requires_specialist (true if lawyer/DPO/security pro is needed)\n"
            " - legal_blockers (anything that prevents launch in target geography)\n"
            "Then still produce: technical findings, prompt-injection risks, "
            "auth recommendations. Frame everything for a founder making a "
            "go/no-go decision, not for engineers."
        )

    def progress_steps(self, ctx: dict) -> list[str]:
        return [
            "Mapping regulatory triggers (GDPR/LGPD/PCI/HIPAA)...",
            "Identifying legal blockers in target geography...",
            "Estimating compliance lead times...",
            "Surfacing technical findings...",
        ]

    def build_artifacts(self, output: SecurityOutput, ctx: dict) -> list[ArtifactBase]:  # type: ignore[override]
        compliance = "\n".join(
            f"### {c.title}\n- **Applies when:** {c.applies_when}\n"
            f"- **Lead time:** {c.lead_time_weeks or '—'}" + (f"\n- {c.notes}" if c.notes else "")
            for c in output.compliance_requirements
        )
        findings = "\n".join(
            f"### {f.title}\n- **Severity:** {f.severity.value.upper()} · **Category:** {f.category}\n"
            f"- {f.description}\n- _Recommendation:_ {f.recommendation}"
            for f in output.findings
        )

        specialist_line = (
            "⚠️ **Specialist required** — engage a lawyer / DPO / security pro before launch."
            if output.requires_specialist
            else "_No specialist required at this stage._"
        )

        header = f"**Overall risk:** {output.overall_risk.value.upper()} · {specialist_line}\n\n"
        if compliance:
            header += f"## Compliance Requirements\n{compliance}\n\n"
        if output.legal_blockers:
            header += f"## Legal Blockers\n{self._bullets(output.legal_blockers)}\n\n"

        md = (
            f"# Compliance & Legal Review\n\n"
            f"{header}"
            f"## Technical Findings\n{findings or '_None._'}\n\n"
            f"## Prompt Injection Risks\n{self._bullets(output.prompt_injection_risks)}\n\n"
            f"## Auth Recommendations\n{self._bullets(output.auth_recommendations)}\n\n"
            f"## Compliance Notes\n{self._bullets(output.compliance_notes)}\n"
        )
        return [
            ArtifactBase(
                title="Compliance & Legal Review",
                path="docs/06-security-review.md",
                kind=ArtifactKind.REPORT,
                produced_by=self.role,
                content=md,
                summary=(f"{len(output.compliance_requirements)} compliance items · risk: {output.overall_risk.value}"),
            )
        ]
