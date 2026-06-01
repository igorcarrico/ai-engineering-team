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


# --------------------------------------------------------------------------- #
# Per-agent outputs
# --------------------------------------------------------------------------- #


class ProductManagerOutput(BaseModel):
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
    architecture_overview: str
    architecture_style: str
    components: list[Component] = Field(default_factory=list)
    data_model: list[Entity] = Field(default_factory=list)
    api_endpoints: list[ApiEndpoint] = Field(default_factory=list)
    infrastructure: list[str] = Field(default_factory=list)
    scalability_notes: list[str] = Field(default_factory=list)
    tech_stack: dict[str, str] = Field(default_factory=dict)


class BackendEngineerOutput(BaseModel):
    service_modules: list[ServiceModule] = Field(default_factory=list)
    endpoints: list[ApiEndpoint] = Field(default_factory=list)
    files: list[GeneratedFile] = Field(default_factory=list)
    implementation_notes: list[str] = Field(default_factory=list)


class FrontendEngineerOutput(BaseModel):
    pages: list[PageSpec] = Field(default_factory=list)
    components: list[ComponentSpec] = Field(default_factory=list)
    state_management: str
    files: list[GeneratedFile] = Field(default_factory=list)
    implementation_notes: list[str] = Field(default_factory=list)


class QAOutput(BaseModel):
    test_strategy: str
    test_scenarios: list[TestScenario] = Field(default_factory=list)
    edge_cases: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    qa_checklist: list[ChecklistItem] = Field(default_factory=list)
    risk_areas: list[str] = Field(default_factory=list)


class SecurityOutput(BaseModel):
    overall_risk: Severity
    findings: list[SecurityFinding] = Field(default_factory=list)
    prompt_injection_risks: list[str] = Field(default_factory=list)
    auth_recommendations: list[str] = Field(default_factory=list)
    compliance_notes: list[str] = Field(default_factory=list)


class CodeReviewOutput(BaseModel):
    verdict: ReviewVerdict
    score: int = Field(ge=0, le=100, description="Overall engineering quality score")
    overall_assessment: str
    strengths: list[str] = Field(default_factory=list)
    issues: list[ReviewIssue] = Field(default_factory=list)
    consistency_checks: list[str] = Field(default_factory=list)
    revision_focus: list[str] = Field(
        default_factory=list,
        description="If verdict is REVISE, what the next iteration should focus on",
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
