"""Deterministic, idea-tailored mock outputs for every agent.

This is what lets the entire platform run end-to-end with zero API keys while
still producing content that reads like a real engineering team's work. Output
is a pure function of (idea, constraints, prior outputs), so demos are
reproducible and tests are stable.
"""

from __future__ import annotations

import re

from app.schemas.agent_io import (
    ApiEndpoint,
    ArchitectOutput,
    BackendEngineerOutput,
    ChecklistItem,
    CodeReviewOutput,
    Component,
    ComponentSpec,
    Entity,
    FrontendEngineerOutput,
    GeneratedFile,
    PageSpec,
    ProductManagerOutput,
    QAOutput,
    ReviewIssue,
    Risk,
    SecurityFinding,
    SecurityOutput,
    ServiceModule,
    TestScenario,
    UserStory,
)
from app.schemas.enums import Priority, ReviewVerdict, Severity

_STOPWORDS = {
    "a",
    "an",
    "the",
    "for",
    "to",
    "of",
    "and",
    "with",
    "build",
    "create",
    "make",
    "platform",
    "app",
    "application",
    "system",
    "that",
    "powered",
    "using",
    "based",
    "ai",
}


def derive(idea: str, name: str | None) -> dict[str, str | list[str]]:
    """Extract a few stable descriptors from the raw idea string."""
    words = re.findall(r"[A-Za-z][A-Za-z0-9+]+", idea)
    keywords = [w for w in words if w.lower() not in _STOPWORDS]
    primary = keywords[:4] or ["Product"]
    product_name = name or (" ".join(w.capitalize() for w in primary[:3]) or "Product")
    slug = re.sub(r"[^a-z0-9]+", "-", product_name.lower()).strip("-") or "product"
    domain = keywords[0].capitalize() if keywords else "Product"
    return {
        "product_name": product_name,
        "slug": slug,
        "domain": domain,
        "keywords": keywords[:6],
        "idea": idea.strip(),
    }


# --------------------------------------------------------------------------- #
# Product Manager
# --------------------------------------------------------------------------- #


def product_manager(ctx: dict) -> ProductManagerOutput:
    d = ctx["_derived"]
    name = d["product_name"]
    domain = d["domain"]
    return ProductManagerOutput(
        product_vision=(
            f"{name} is a {domain.lower()}-focused platform that turns the goal "
            f"“{d['idea']}” into a focused, shippable product. The MVP "
            f"validates the core loop with a small set of high-leverage features "
            f"before investing in breadth."
        ),
        target_users=[
            f"Primary: {domain} operators who need faster, data-backed decisions",
            "Secondary: team leads who manage workflows and review outcomes",
            "Tertiary: administrators configuring access, billing and integrations",
        ],
        user_stories=[
            UserStory(
                as_a="new user",
                i_want="to sign up and reach a useful first result in under 5 minutes",
                so_that="I can evaluate the product without friction",
                priority=Priority.HIGH,
            ),
            UserStory(
                as_a="power user",
                i_want="to save, revisit and compare my past results",
                so_that="I can build on previous work instead of starting over",
                priority=Priority.HIGH,
            ),
            UserStory(
                as_a="team lead",
                i_want="to invite teammates and assign roles",
                so_that="my team can collaborate with the right permissions",
                priority=Priority.MEDIUM,
            ),
            UserStory(
                as_a="administrator",
                i_want="to monitor usage and manage billing",
                so_that="I can keep the account healthy and within budget",
                priority=Priority.MEDIUM,
            ),
        ],
        mvp_scope=[
            "Authentication and basic account management",
            f"Core {domain.lower()} workflow producing a tangible primary output",
            "Persistent history of results with search/filter",
            "Export of results (PDF/CSV/JSON)",
            "Usage dashboard with key metrics",
        ],
        out_of_scope=[
            "Native mobile apps (responsive web only for MVP)",
            "Advanced role hierarchies beyond admin/member",
            "Marketplace / third-party plugin ecosystem",
            "On-prem / self-hosted deployment",
        ],
        assumptions=[
            "Users are comfortable working in a web application",
            "A managed cloud deployment is acceptable for the MVP",
            "English is sufficient for the first release; i18n comes later",
            "Third-party data sources expose stable, documented APIs",
        ],
        risks=[
            Risk(
                description="Unclear primary value metric could blur the MVP scope",
                severity=Severity.MEDIUM,
                mitigation="Define one north-star metric and instrument it from day one",
            ),
            Risk(
                description="LLM/processing cost may scale faster than revenue",
                severity=Severity.HIGH,
                mitigation="Add per-tenant quotas, caching and tiered pricing early",
            ),
            Risk(
                description="Data privacy expectations in this domain may be strict",
                severity=Severity.HIGH,
                mitigation="Adopt least-privilege access and encryption from the start",
            ),
        ],
        success_metrics=[
            "Time-to-first-value < 5 minutes for new users",
            "Week-1 retention ≥ 35%",
            "≥ 60% of active users export or share a result",
            "Gross margin per active user trending positive by month 3",
        ],
        technical_requirements=[
            "Multi-tenant data isolation",
            "Async processing for long-running jobs with progress feedback",
            "Audit log of sensitive actions",
            "Horizontal scalability of the processing layer",
            "Observability: structured logs, metrics and tracing",
        ],
    )


# --------------------------------------------------------------------------- #
# Architect
# --------------------------------------------------------------------------- #


def architect(ctx: dict) -> ArchitectOutput:
    d = ctx["_derived"]
    name = d["product_name"]
    return ArchitectOutput(
        architecture_overview=(
            f"{name} adopts a modular monolith for the MVP: a single deployable "
            "backend split into clear bounded contexts (auth, core workflow, "
            "billing, integrations) with a separate async worker for heavy jobs. "
            "This keeps operational cost low while leaving clean seams to extract "
            "services later."
        ),
        architecture_style="Modular monolith + async workers (extractable to services)",
        components=[
            Component(name="API Gateway", responsibility="HTTP API, auth, rate limiting", technology="FastAPI"),
            Component(
                name="Core Service", responsibility="Primary domain workflow and orchestration", technology="Python"
            ),
            Component(
                name="Worker", responsibility="Async/long-running processing jobs", technology="Python + task queue"
            ),
            Component(name="Web App", responsibility="User-facing SPA", technology="Next.js + TypeScript"),
            Component(name="Datastore", responsibility="Relational persistence + migrations", technology="PostgreSQL"),
            Component(name="Cache/Queue", responsibility="Caching and job brokering", technology="Redis"),
        ],
        data_model=[
            Entity(
                name="User",
                fields=["id", "email", "password_hash", "role", "created_at"],
                relationships=["belongs_to Organization"],
            ),
            Entity(
                name="Organization",
                fields=["id", "name", "plan", "created_at"],
                relationships=["has_many User", "has_many Project"],
            ),
            Entity(
                name="Project",
                fields=["id", "org_id", "name", "config_json", "created_at"],
                relationships=["has_many Job"],
            ),
            Entity(
                name="Job",
                fields=["id", "project_id", "status", "result_json", "started_at", "finished_at"],
                relationships=["belongs_to Project"],
            ),
            Entity(
                name="AuditLog",
                fields=["id", "actor_id", "action", "target", "created_at"],
                relationships=["belongs_to User"],
            ),
        ],
        api_endpoints=[
            ApiEndpoint(method="POST", path="/api/auth/register", description="Create account", auth_required=False),
            ApiEndpoint(
                method="POST", path="/api/auth/login", description="Authenticate and issue tokens", auth_required=False
            ),
            ApiEndpoint(method="GET", path="/api/projects", description="List projects for the org"),
            ApiEndpoint(method="POST", path="/api/projects", description="Create a project"),
            ApiEndpoint(method="POST", path="/api/projects/{id}/jobs", description="Start a processing job"),
            ApiEndpoint(method="GET", path="/api/jobs/{id}", description="Fetch job status and result"),
        ],
        infrastructure=[
            "Containerized with Docker, orchestrated via Compose (MVP) → Kubernetes (scale)",
            "Managed PostgreSQL with automated backups and PITR",
            "Managed Redis for cache + job queue",
            "Object storage (S3-compatible) for exported artifacts",
            "CI/CD with automated tests, linting and image builds",
        ],
        scalability_notes=[
            "Stateless API replicas behind a load balancer",
            "Workers scale independently based on queue depth",
            "Read replicas + query caching for read-heavy endpoints",
            "Per-tenant rate limits to protect shared resources",
        ],
        tech_stack={
            "backend": "FastAPI (Python)",
            "frontend": "Next.js + TypeScript + Tailwind",
            "database": "PostgreSQL",
            "cache_queue": "Redis",
            "infra": "Docker / Kubernetes",
        },
    )


# --------------------------------------------------------------------------- #
# Backend Engineer
# --------------------------------------------------------------------------- #


def backend_engineer(ctx: dict) -> BackendEngineerOutput:
    d = ctx["_derived"]
    slug = d["slug"]
    return BackendEngineerOutput(
        service_modules=[
            ServiceModule(
                name="auth",
                responsibility="Registration, login, JWT issuance, RBAC",
                key_functions=["register_user", "authenticate", "require_role"],
            ),
            ServiceModule(
                name="projects",
                responsibility="CRUD for projects and configuration",
                key_functions=["create_project", "list_projects", "update_config"],
            ),
            ServiceModule(
                name="jobs",
                responsibility="Enqueue, track and persist processing jobs",
                key_functions=["enqueue_job", "get_job", "mark_complete"],
            ),
            ServiceModule(
                name="billing",
                responsibility="Plans, quotas and usage metering",
                key_functions=["check_quota", "record_usage"],
            ),
        ],
        endpoints=[
            ApiEndpoint(method="POST", path="/api/projects/{id}/jobs", description="Create and enqueue a job"),
            ApiEndpoint(method="GET", path="/api/jobs/{id}", description="Poll job status/result"),
            ApiEndpoint(method="GET", path="/api/usage", description="Return current usage vs quota"),
        ],
        files=[
            GeneratedFile(
                path="backend/app/services/jobs_service.py",
                language="python",
                description="Service layer that enqueues and tracks processing jobs",
                content=(
                    "from __future__ import annotations\n\n"
                    "from app.repositories.job_repo import JobRepository\n"
                    "from app.schemas import JobCreate, JobRead\n\n\n"
                    "class JobsService:\n"
                    "    def __init__(self, repo: JobRepository, queue) -> None:\n"
                    "        self._repo = repo\n"
                    "        self._queue = queue\n\n"
                    "    async def enqueue(self, project_id: str, payload: JobCreate) -> JobRead:\n"
                    "        job = await self._repo.create(project_id, payload)\n"
                    '        await self._queue.publish("jobs", {"job_id": job.id})\n'
                    "        return job\n\n"
                    "    async def get(self, job_id: str) -> JobRead | None:\n"
                    "        return await self._repo.get(job_id)\n"
                ),
            ),
            GeneratedFile(
                path="backend/app/routers/jobs.py",
                language="python",
                description="FastAPI router exposing job endpoints",
                content=(
                    "from fastapi import APIRouter, Depends\n\n"
                    "from app.schemas import JobCreate, JobRead\n"
                    "from app.services.jobs_service import JobsService\n"
                    "from app.deps import get_jobs_service\n\n"
                    'router = APIRouter(prefix="/api", tags=["jobs"])\n\n\n'
                    '@router.post("/projects/{project_id}/jobs", response_model=JobRead)\n'
                    "async def create_job(project_id: str, body: JobCreate,\n"
                    "                     svc: JobsService = Depends(get_jobs_service)):\n"
                    "    return await svc.enqueue(project_id, body)\n"
                ),
            ),
        ],
        implementation_notes=[
            "Use dependency injection so services are unit-testable without a DB",
            "All long-running work goes through the queue, never inline in a request",
            "Return 202 + a job id for async work; clients poll or subscribe via SSE",
            f"Namespace storage buckets per tenant, e.g. s3://{slug}/<org_id>/...",
        ],
    )


# --------------------------------------------------------------------------- #
# Frontend Engineer
# --------------------------------------------------------------------------- #


def frontend_engineer(ctx: dict) -> FrontendEngineerOutput:
    return FrontendEngineerOutput(
        pages=[
            PageSpec(route="/", name="Landing", description="Marketing + sign up CTA"),
            PageSpec(route="/login", name="Login", description="Authentication"),
            PageSpec(route="/dashboard", name="Dashboard", description="Overview of projects and usage"),
            PageSpec(route="/projects/[id]", name="Project Detail", description="Run jobs and view results"),
            PageSpec(route="/settings", name="Settings", description="Account, team and billing"),
        ],
        components=[
            ComponentSpec(name="AppShell", description="Sidebar + top bar layout", props=["children"]),
            ComponentSpec(name="ResultCard", description="Displays a single job result", props=["job", "onExport"]),
            ComponentSpec(name="JobProgress", description="Live progress indicator for async jobs", props=["jobId"]),
            ComponentSpec(name="UsageMeter", description="Quota usage visualization", props=["used", "limit"]),
        ],
        state_management=(
            "React Server Components for data fetching + lightweight client store "
            "(Zustand) for ephemeral UI state"
        ),
        files=[
            GeneratedFile(
                path="frontend/src/components/JobProgress.tsx",
                language="tsx",
                description="Subscribes to job progress and renders a live status bar",
                content=(
                    '"use client";\n\n'
                    'import { useJobStream } from "@/hooks/useJobStream";\n\n'
                    "export function JobProgress({ jobId }: { jobId: string }) {\n"
                    "  const { status, progress } = useJobStream(jobId);\n"
                    "  return (\n"
                    '    <div className="space-y-2">\n'
                    '      <p className="text-sm text-muted-foreground">{status}</p>\n'
                    '      <div className="h-2 w-full rounded bg-muted">\n'
                    '        <div className="h-2 rounded bg-primary transition-all"\n'
                    "             style={{ width: `${progress}%` }} />\n"
                    "      </div>\n"
                    "    </div>\n"
                    "  );\n"
                    "}\n"
                ),
            ),
        ],
        implementation_notes=[
            "Prefer server components for data; mark interactive leaves as client",
            "Co-locate API types with a typed fetch client to avoid drift",
            "Every async action needs explicit loading, empty and error states",
        ],
    )


# --------------------------------------------------------------------------- #
# QA Engineer
# --------------------------------------------------------------------------- #


def qa_engineer(ctx: dict) -> QAOutput:
    return QAOutput(
        test_strategy=(
            "Testing pyramid: many fast unit tests around services and pure logic, "
            "a focused set of integration tests across the API + database, and a "
            "thin layer of end-to-end smoke tests for the critical user journey."
        ),
        test_scenarios=[
            TestScenario(
                title="New user happy path",
                type="e2e",
                steps=["Register", "Create project", "Run a job", "View result"],
                expected="A result is produced and visible within the SLA",
            ),
            TestScenario(
                title="Quota exceeded",
                type="integration",
                steps=["Consume quota", "Attempt new job"],
                expected="Request is rejected with 402 and a clear message",
            ),
            TestScenario(
                title="Concurrent jobs",
                type="integration",
                steps=["Submit N jobs simultaneously"],
                expected="All jobs are tracked independently; none are lost",
            ),
            TestScenario(
                title="Auth boundary",
                type="unit",
                steps=["Call protected endpoint without/with wrong role"],
                expected="401/403 returned; no data leaks",
            ),
        ],
        edge_cases=[
            "Empty or malformed input payloads",
            "Extremely large inputs near payload limits",
            "Job that fails midway — partial state must be recoverable",
            "Token expiry during a long-running session",
            "Duplicate submissions (idempotency)",
        ],
        missing_requirements=[
            "Idempotency keys for job creation are not yet specified",
            "Data retention / deletion policy is undefined",
            "Rate-limit response contract (headers, status) needs definition",
        ],
        qa_checklist=[
            ChecklistItem(item="All endpoints have input validation", category="validation"),
            ChecklistItem(item="Error responses use a consistent schema", category="api"),
            ChecklistItem(item="DB migrations run cleanly forward and back", category="data"),
            ChecklistItem(item="Critical paths covered by automated tests", category="testing"),
            ChecklistItem(item="Loading/empty/error states exist in UI", category="ux"),
        ],
        risk_areas=[
            "Async job lifecycle (the most stateful, failure-prone area)",
            "Multi-tenant data isolation",
            "Quota/billing accuracy under concurrency",
        ],
    )


# --------------------------------------------------------------------------- #
# Security Reviewer
# --------------------------------------------------------------------------- #


def security_reviewer(ctx: dict) -> SecurityOutput:
    return SecurityOutput(
        overall_risk=Severity.MEDIUM,
        findings=[
            SecurityFinding(
                title="Tenant isolation must be enforced at the query layer",
                category="authz",
                severity=Severity.HIGH,
                description="Without row-level scoping, a bug could leak cross-tenant data.",
                recommendation=(
                    "Scope every query by org_id via a repository base class; add tests "
                    "that assert isolation."
                ),
            ),
            SecurityFinding(
                title="Secrets in environment, not in code",
                category="infra",
                severity=Severity.MEDIUM,
                description="API keys and DB creds must never be committed.",
                recommendation="Use a secrets manager; keep .env out of VCS; rotate keys.",
            ),
            SecurityFinding(
                title="Input validation on all external boundaries",
                category="injection",
                severity=Severity.MEDIUM,
                description="Unvalidated input can lead to injection or resource abuse.",
                recommendation="Validate with Pydantic; parametrize all DB access; cap payload sizes.",
            ),
            SecurityFinding(
                title="Untrusted text reaches the LLM",
                category="prompt",
                severity=Severity.MEDIUM,
                description="User content used in prompts can attempt prompt injection.",
                recommendation=(
                    "Treat model output as untrusted; never execute it; isolate system "
                    "prompts; constrain with structured outputs."
                ),
            ),
        ],
        prompt_injection_risks=[
            "User-supplied text concatenated into system prompts",
            "Model output used to drive actions without validation",
            "Indirect injection via fetched third-party content",
        ],
        auth_recommendations=[
            "Short-lived access tokens + rotating refresh tokens",
            "Hash passwords with a slow KDF (argon2/bcrypt)",
            "Enforce RBAC on every endpoint, deny-by-default",
            "Audit-log all sensitive actions",
        ],
        compliance_notes=[
            "Document data retention and a deletion (GDPR-style) path",
            "Encrypt data at rest and in transit",
            "Provide a data-processing record for B2B customers",
        ],
    )


# --------------------------------------------------------------------------- #
# Code Reviewer (drives the conditional refine loop)
# --------------------------------------------------------------------------- #


def code_reviewer(ctx: dict) -> CodeReviewOutput:
    iteration = int(ctx.get("iteration", 0))
    # First pass requests a refinement; subsequent passes approve. This makes the
    # conditional graph loop observable in every demo without being random.
    if iteration < 1:
        return CodeReviewOutput(
            verdict=ReviewVerdict.REVISE,
            score=78,
            overall_assessment=(
                "Strong, coherent plan with a clear MVP. A few cross-cutting gaps "
                "should be closed before this is implementation-ready."
            ),
            strengths=[
                "Tight MVP scope aligned to a single core loop",
                "Clean modular-monolith architecture with extractable seams",
                "Security concerns identified early (tenant isolation, prompt injection)",
            ],
            issues=[
                ReviewIssue(
                    title="Idempotency for job creation is unspecified",
                    area="backend_engineer",
                    severity=Severity.MEDIUM,
                    recommendation="Add idempotency keys and document the retry contract.",
                ),
                ReviewIssue(
                    title="Data retention/deletion policy missing",
                    area="product_manager",
                    severity=Severity.MEDIUM,
                    recommendation="Define retention windows and a deletion path in scope.",
                ),
                ReviewIssue(
                    title="Rate-limit response contract undefined",
                    area="architect",
                    severity=Severity.LOW,
                    recommendation="Specify status code and headers for throttled requests.",
                ),
            ],
            consistency_checks=[
                "PM success metrics map to instrumented events — OK",
                "Architect endpoints align with backend modules — OK",
                "QA risk areas overlap security findings — OK, reinforce in tests",
            ],
            revision_focus=[
                "Refine architecture to specify idempotency and rate-limit contracts",
                "Tighten the data lifecycle story",
            ],
        )
    return CodeReviewOutput(
        verdict=ReviewVerdict.APPROVE,
        score=91,
        overall_assessment=(
            "Revision addressed the flagged gaps. The plan is coherent, secure by "
            "design and implementation-ready for an MVP."
        ),
        strengths=[
            "Idempotency and rate-limit contracts now specified",
            "Clear data lifecycle and retention story",
            "End-to-end consistency across PM → architecture → engineering → QA",
        ],
        issues=[
            ReviewIssue(
                title="Minor: add load tests before GA",
                area="qa_engineer",
                severity=Severity.LOW,
                recommendation="Establish a baseline performance budget pre-launch.",
            ),
        ],
        consistency_checks=[
            "All prior revision items resolved",
            "No contradictions detected across agent outputs",
        ],
        revision_focus=[],
    )


GENERATORS = {
    "product_manager": product_manager,
    "architect": architect,
    "backend_engineer": backend_engineer,
    "frontend_engineer": frontend_engineer,
    "qa_engineer": qa_engineer,
    "security_reviewer": security_reviewer,
    "code_reviewer": code_reviewer,
}
