# Architecture

This document explains how **AI Engineering Team** is put together and why.

## 1. System overview

```
┌──────────────────────────┐         SSE (live activity)        ┌───────────────────────────┐
│        Frontend          │ ◀───────────────────────────────── │          Backend          │
│  Next.js · TS · Tailwind │                                    │   FastAPI · LangGraph     │
│                          │ ──── REST (create / read / export) ▶ │                           │
│  • Create panel          │                                    │  • API routers            │
│  • Run dashboard         │                                    │  • Orchestration service  │
│  • Activity feed (SSE)   │                                    │  • LangGraph workflow     │
│  • Workflow graph        │                                    │  • 7 specialized agents   │
│  • Artifact explorer     │                                    │  • LLM provider abstraction│
└──────────────────────────┘                                    └────────────┬──────────────┘
                                                                              │
                                                              ┌───────────────┴───────────────┐
                                                              │   PostgreSQL / SQLite          │
                                                              │   projects · runs · events ·   │
                                                              │   artifacts                    │
                                                              └────────────────────────────────┘
```

The two halves are decoupled: the browser talks to the backend only through a
small REST surface plus one Server-Sent Events stream. In development, Next.js
proxies `/api/*` to the backend, so the browser always uses same-origin URLs.

## 2. Backend layering

The backend follows a clean, dependency-inverted layering:

```
api/            HTTP routers + FastAPI dependencies (thin)
services/       use-cases: orchestration, projects, artifacts, serializers
graph/          LangGraph workflow: state, nodes, routing, builder
agents/         specialized agents (domain behavior + artifact rendering)
llm/            provider abstraction (mock / anthropic / openai) + factory
repositories/   data access over SQLAlchemy sessions
models/         ORM models
schemas/        Pydantic DTOs + structured agent outputs + events
core/           cross-cutting infra (event hub / emitter)
db/             engine + session management
config.py       typed settings
```

Key rule: **dependencies point inward**. Agents depend on the `LLMProvider`
interface, never a concrete SDK. Routers depend on services; services depend on
repositories and the graph. Nothing in `graph/` or `agents/` imports FastAPI.

## 3. The agents

Seven specialized agents, each with a typed output contract
(`schemas/agent_io.py`) and its own artifact rendering:

| Agent | Output schema | Produces |
|---|---|---|
| Product Manager | `ProductManagerOutput` | Vision, user stories, MVP scope, risks |
| Software Architect | `ArchitectOutput` | Architecture, data model, API surface, Mermaid diagram |
| Backend Engineer | `BackendEngineerOutput` | Service modules, endpoints, starter code |
| Frontend Engineer | `FrontendEngineerOutput` | Pages, components, starter UI code |
| QA Engineer | `QAOutput` | Test strategy, scenarios, checklist, gaps |
| Security Reviewer | `SecurityOutput` | Findings, prompt-injection risks, auth advice |
| Code Reviewer | `CodeReviewOutput` | Verdict (approve/revise), score, issues |

An eighth role, the **Supervisor**, is the orchestration itself (the graph plus
the `refine`/`finalize` control nodes), surfaced in the UI as a distinct actor.

## 4. Structured outputs everywhere

The system never depends on free-form model text. Every agent returns a
Pydantic model:

- With **real providers**, this is enforced via LangChain's
  `with_structured_output(schema)` (tool/JSON-schema constrained decoding).
- With the **mock provider**, deterministic generators in `llm/mock_data.py`
  return the same typed shapes, tailored to the idea.

Downstream code (artifact rendering, persistence, the API) only ever sees typed
objects — which is why the whole platform is testable and provider-portable.

## 5. Persistence

SQLAlchemy 2.0 (async) with four tables: `projects`, `runs`, `run_events`,
`artifacts`. SQLite is the zero-config default (WAL + busy-timeout so the
concurrent writes from parallel graph nodes don't lock); Postgres is a drop-in
via `DATABASE_URL` and is what `docker-compose` uses.

The **event log is the source of truth** for the agent timeline: per-agent step
status and timing are *derived* from persisted events rather than stored
separately, so the UI can never drift from what actually happened.

## 6. Streaming & observability

- A process-wide `EventHub` (in `core/events.py`) is a tiny pub/sub. Graph nodes
  emit `RunEvent`s through an `EventEmitter`; each event is persisted **and**
  published to subscribers.
- The SSE endpoint (`GET /api/runs/{id}/stream`) subscribes first, replays the
  buffer/DB (de-duplicating by id), then streams live until a finish sentinel —
  so a client that joins late still sees the full timeline with no gaps.
- Runs execute as background `asyncio` tasks; creating a run returns immediately.

## 7. Provider abstraction

`LLMProvider` is a 1-method async interface (`generate(system, prompt, schema,
context) -> BaseModel`). `build_provider()` resolves the configured provider and
**falls back to mock** (with a warning) if a real provider is requested without
credentials — so a misconfigured demo degrades instead of crashing.

## 8. Why these choices

- **Modular monolith** backend: fastest path to a coherent, demoable system with
  clean seams (the `graph/`, `agents/`, `llm/` packages) to extract later.
- **LangGraph** over a hand-rolled loop: real stateful orchestration —
  parallelism, a join, a bounded conditional loop, and a checkpointer — that is
  inspectable and extensible.
- **Mock-first**: a flagship portfolio project must run instantly for anyone who
  clones it. Determinism also makes the test suite stable.
