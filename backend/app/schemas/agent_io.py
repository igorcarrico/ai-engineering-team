"""Structured output schemas for every agent.

These models are the *contract* each agent must satisfy. With real providers
they are produced via structured-output / tool-calling; with the mock provider
they are generated deterministically. Either way the rest of the system depends
only on these typed shapes — never on raw model text.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.enums import Priority, ReviewVerdict, Severity

# --------------------------------------------------------------------------- #
# Shared building blocks
# --------------------------------------------------------------------------- #


class UserStory(BaseModel):
    as_a: str = Field(description="The persona / role")
    i_want: str = Field(description="The capability they want")
    so_that: str = Field(description="The value they get")
    priority: Priority = Priority.MEDIUM


class Risk(BaseModel):
    description: str
    severity: Severity = Severity.MEDIUM
    mitigation: str


class Component(BaseModel):
    name: str
    responsibility: str
    technology: str


class Entity(BaseModel):
    name: str
    fields: list[str] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)


class ApiEndpoint(BaseModel):
    method: str
    path: str
    description: str
    auth_required: bool = True


class ServiceModule(BaseModel):
    name: str
    responsibility: str
    key_functions: list[str] = Field(default_factory=list)


class PageSpec(BaseModel):
    route: str
    name: str
    description: str


class ComponentSpec(BaseModel):
    name: str
    description: str
    props: list[str] = Field(default_factory=list)


class TestScenario(BaseModel):
    title: str
    type: str = Field(description="unit | integration | e2e")
    steps: list[str] = Field(default_factory=list)
    expected: str


class ChecklistItem(BaseModel):
    item: str
    category: str


class SecurityFinding(BaseModel):
    title: str
    category: str = Field(description="authn | authz | injection | data | infra | prompt")
    severity: Severity
    description: str
    recommendation: str


class ReviewIssue(BaseModel):
    title: str
    area: str = Field(description="Which agent's output the issue concerns")
    severity: Severity
    recommendation: str


class GeneratedFile(BaseModel):
    """A file artifact an engineering agent proposes to create."""

    path: str
    language: str
    description: str
    content: str


class BuildVsBuy(BaseModel):
    """For each capability, recommend building custom vs adopting an existing solution."""

    capability: str = Field(description="The capability/feature being decided on")
    recommendation: str = Field(description="build | buy | hybrid")
    why: str
    suggested_vendor: str = Field(default="", description="If buy/hybrid, a concrete vendor or category")


class ComplianceRequirement(BaseModel):
    """A regulatory/legal requirement the founder must plan for."""

    title: str
    applies_when: str = Field(description="The trigger condition, e.g. 'EU users', 'card payments'")
    lead_time_weeks: str = Field(default="", description="Rough effort, e.g. '2-4 weeks', 'requires lawyer'")
    notes: str = Field(default="")


# --------------------------------------------------------------------------- #
# Per-agent outputs
# --------------------------------------------------------------------------- #


class ProductManagerOutput(BaseModel):
    # Feasibility framing fields (lead the output for non-technical founders)
    value_proposition: str = Field(
        default="",
        description="One-sentence elevator pitch a founder would say to an investor",
    )
    primary_metric_target: str = Field(
        default="",
        description="The single most important metric + a concrete target (e.g. '10% fuel cost reduction in 90 days')",
    )
    # Existing fields
    product_vision: str
    target_users: list[str] = Field(default_factory=list)
    user_stories: list[UserStory] = Field(default_factory=list)
    mvp_scope: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    risks: list[Risk] = Field(default_factory=list)
    success_metrics: list[str] = Field(default_factory=list)
    technical_requirements: list[str] = Field(default_factory=list)


class ArchitectOutput(BaseModel):
    # Feasibility framing
    complexity_rating: str = Field(
        default="moderate",
        description="One of: simple | moderate | complex | very_complex",
    )
    complexity_drivers: list[str] = Field(
        default_factory=list,
        description="The 2-4 things that make this hard to build (integrations, scale, novelty, regulation, etc.)",
    )
    build_vs_buy: list[BuildVsBuy] = Field(
        default_factory=list,
        description="For each major capability, recommend custom-build vs adopting an existing SaaS",
    )
    # Existing fields
    architecture_overview: str
    architecture_style: str
    components: list[Component] = Field(default_factory=list)
    data_model: list[Entity] = Field(default_factory=list)
    api_endpoints: list[ApiEndpoint] = Field(default_factory=list)
    infrastructure: list[str] = Field(default_factory=list)
    scalability_notes: list[str] = Field(default_factory=list)
    tech_stack: dict[str, str] = Field(default_factory=dict)


class BackendEngineerOutput(BaseModel):
    # Feasibility framing
    effort_estimate: str = Field(
        default="",
        description="Ballpark like '4-6 weeks' or '2-3 months' for the backend MVP",
    )
    team_needed: str = Field(
        default="",
        description="Skill level and headcount, e.g. '1 senior backend engineer'",
    )
    # Existing fields
    service_modules: list[ServiceModule] = Field(default_factory=list)
    endpoints: list[ApiEndpoint] = Field(default_factory=list)
    files: list[GeneratedFile] = Field(default_factory=list)
    implementation_notes: list[str] = Field(default_factory=list)


class FrontendEngineerOutput(BaseModel):
    # Feasibility framing
    effort_estimate: str = Field(
        default="",
        description="Ballpark like '4-6 weeks' for the frontend MVP",
    )
    team_needed: str = Field(
        default="",
        description="Skill level and headcount, e.g. '1 mid-level frontend + 0.5 designer'",
    )
    # Existing fields
    pages: list[PageSpec] = Field(default_factory=list)
    components: list[ComponentSpec] = Field(default_factory=list)
    state_management: str = Field(default="")
    files: list[GeneratedFile] = Field(default_factory=list)
    implementation_notes: list[str] = Field(default_factory=list)


class QAOutput(BaseModel):
    # Feasibility framing
    quality_floor: list[str] = Field(
        default_factory=list,
        description="The minimum quality bar; skipping these will burn users on day one",
    )
    failure_modes: list[str] = Field(
        default_factory=list,
        description="Top 3 reasons this product would fail to launch or get adopted",
    )
    # Existing fields
    test_strategy: str
    test_scenarios: list[TestScenario] = Field(default_factory=list)
    edge_cases: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    qa_checklist: list[ChecklistItem] = Field(default_factory=list)
    risk_areas: list[str] = Field(default_factory=list)


class SecurityOutput(BaseModel):
    overall_risk: Severity
    # Feasibility framing
    compliance_requirements: list[ComplianceRequirement] = Field(
        default_factory=list,
        description="Concrete legal/regulatory items the founder must plan for (GDPR, PCI, HIPAA, LGPD, etc.)",
    )
    requires_specialist: bool = Field(
        default=False,
        description="True if a lawyer, DPO, or security consultant is needed before launch",
    )
    legal_blockers: list[str] = Field(
        default_factory=list,
        description="Anything that could block launch in target geography",
    )
    # Existing fields
    findings: list[SecurityFinding] = Field(default_factory=list)
    prompt_injection_risks: list[str] = Field(default_factory=list)
    auth_recommendations: list[str] = Field(default_factory=list)
    compliance_notes: list[str] = Field(default_factory=list)


class CodeReviewOutput(BaseModel):
    """The founder-facing verdict: GO / GO_WITH_CONDITIONS / NO_GO.

    Acts as both the engineering review (verdict + score, for the refine loop)
    AND the executive decision card the non-technical founder reads first.
    """

    # --- Engineering review (drives the iteration loop) ---
    verdict: ReviewVerdict
    score: int = Field(ge=0, le=100, description="Plan quality score 0-100")
    overall_assessment: str
    strengths: list[str] = Field(default_factory=list)
    issues: list[ReviewIssue] = Field(default_factory=list)
    consistency_checks: list[str] = Field(default_factory=list)
    revision_focus: list[str] = Field(
        default_factory=list,
        description="If verdict is REVISE, what the next iteration should focus on",
    )

    # --- Founder-facing feasibility verdict ---
    go_no_go: str = Field(
        default="",
        description="GO | GO_WITH_CONDITIONS | NO_GO — the clear recommendation to the founder",
    )
    verdict_rationale: str = Field(
        default="",
        description="One paragraph explaining the go/no-go in plain language for a non-technical founder",
    )
    mvp_timeline: str = Field(
        default="",
        description="Range to ship the MVP (e.g. '6-10 weeks')",
    )
    mvp_budget_usd_range: str = Field(
        default="",
        description="Range to ship the MVP (e.g. '$30k-$50k', or '$0-$5k tooling if solo')",
    )
    v1_timeline: str = Field(
        default="",
        description="Range to reach a polished V1 (e.g. '4-6 months')",
    )
    v1_budget_usd_range: str = Field(
        default="",
        description="Range for V1 total cost (e.g. '$120k-$200k')",
    )
    recommended_team: str = Field(
        default="",
        description="The team composition the founder should hire/assemble",
    )
    top_questions_to_validate_first: list[str] = Field(
        default_factory=list,
        description=(
            "The 3-5 questions the founder should answer BEFORE committing budget — "
            "discovery interviews, prototypes, etc."
        ),
    )
    kill_criteria: list[str] = Field(
        default_factory=list,
        description="Conditions under which the founder should abandon the idea",
    )


# Map of agent key -> output schema, used by the provider/agent layer.
AGENT_OUTPUT_SCHEMAS: dict[str, type[BaseModel]] = {
    "product_manager": ProductManagerOutput,
    "architect": ArchitectOutput,
    "backend_engineer": BackendEngineerOutput,
    "frontend_engineer": FrontendEngineerOutput,
    "qa_engineer": QAOutput,
    "security_reviewer": SecurityOutput,
    "code_reviewer": CodeReviewOutput,
}
