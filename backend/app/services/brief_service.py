"""Render a run's artifacts as a single self-contained HTML brief.

This is the *real* deliverable: instead of a zip of loose markdown files, the
user gets one navigable, polished document they can read in the browser, share
with a stakeholder, or print to PDF.
"""

from __future__ import annotations

import html as html_lib
import re
from datetime import UTC, datetime
from typing import Any

import markdown as md
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import Run
from app.repositories.artifact_repo import ArtifactRepository
from app.repositories.project_repo import ProjectRepository
from app.repositories.run_repo import RunRepository
from app.schemas.enums import AgentRole

# Order in which sections appear in the brief. Anything unknown goes at the end.
SECTION_ORDER = [
    "docs/00-delivery-summary.md",
    "docs/01-product-definition.md",
    "docs/02-architecture.md",
    "docs/02-architecture-diagram.md",
    "docs/03-backend-plan.md",
    "docs/04-frontend-plan.md",
    "docs/05-qa-plan.md",
    "docs/06-security-review.md",
    "docs/07-code-review.md",
]

_MERMAID_PATTERN = re.compile(r'<pre><code class="language-mermaid">(.*?)</code></pre>', re.DOTALL)


class BriefService:
    def __init__(self, session: AsyncSession) -> None:
        self._artifacts = ArtifactRepository(session)
        self._runs = RunRepository(session)
        self._projects = ProjectRepository(session)

    async def render(self, run_id: str) -> str | None:
        run = await self._runs.get(run_id)
        if run is None:
            return None
        project = await self._projects.get(run.project_id)
        artifacts = {a.path: a for a in await self._artifacts.list(run_id)}

        ordered_paths = [p for p in SECTION_ORDER if p in artifacts]
        ordered_paths += sorted(p for p in artifacts if p not in SECTION_ORDER)

        sections: list[dict[str, Any]] = []
        for path in ordered_paths:
            art = artifacts[path]
            agent_label = (
                AgentRole(art.produced_by).label
                if art.produced_by in AgentRole.__members__.values() or art.produced_by in {r.value for r in AgentRole}
                else art.produced_by
            )
            if art.kind == "code":
                body = (
                    f'<pre class="code"><code class="language-'
                    f'{html_lib.escape(art.language)}">'
                    f"{html_lib.escape(art.content)}</code></pre>"
                )
            else:
                body = md.markdown(art.content, extensions=["tables", "fenced_code"])
                # Promote ```mermaid blocks so Mermaid.js renders them as diagrams.
                body = _MERMAID_PATTERN.sub(r'<pre class="mermaid">\1</pre>', body)
            sections.append(
                {
                    "slug": _slug(path),
                    "title": art.title,
                    "path": path,
                    "agent_label": agent_label,
                    "body": body,
                }
            )

        return _build_html(run, project, sections)


def _slug(path: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")


def _fmt_duration(ms: int | None) -> str:
    if ms is None:
        return "—"
    s = ms / 1000
    if s < 60:
        return f"{s:.1f}s"
    return f"{int(s // 60)}m {int(s % 60)}s"


def _build_html(run: Run, project: Any, sections: list[dict[str, Any]]) -> str:
    project_name = project.name if project else "Engineering Brief"
    idea = project.idea if project else ""
    outputs = run.outputs or {}
    review = outputs.get("code_reviewer", {})
    verdict = review.get("verdict", "—")
    score = review.get("score") if review.get("score") is not None else "—"

    status_class = run.status
    verdict_class = verdict if verdict in {"approve", "revise"} else "neutral"

    nav_items = "\n".join(
        f'<a href="#{s["slug"]}" class="nav-item">'
        f'<span class="nav-num">{i + 1:02d}</span>'
        f'<span class="nav-label">{html_lib.escape(s["title"])}</span>'
        f"</a>"
        for i, s in enumerate(sections)
    )

    body_sections = "\n".join(
        f'<section id="{s["slug"]}" class="section">'
        f'<header class="section-head">'
        f"<h2>{html_lib.escape(s['title'])}</h2>"
        f'<div class="section-meta">'
        f'<span class="section-tag">{html_lib.escape(s["agent_label"])}</span>'
        f'<code class="section-path">{html_lib.escape(s["path"])}</code>'
        f"</div>"
        f"</header>"
        f'<div class="section-body">{s["body"]}</div>'
        f"</section>"
        for s in sections
    )

    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    iterations = f"{run.iteration + 1} / {run.max_iterations}"

    return (
        _HTML_SHELL.replace("{{TITLE}}", html_lib.escape(project_name))
        .replace("{{IDEA}}", html_lib.escape(idea))
        .replace("{{STATUS}}", run.status)
        .replace("{{STATUS_CLASS}}", status_class)
        .replace("{{VERDICT}}", html_lib.escape(str(verdict).upper()))
        .replace("{{VERDICT_CLASS}}", verdict_class)
        .replace("{{SCORE}}", str(score))
        .replace("{{ITERATIONS}}", iterations)
        .replace("{{MODEL}}", html_lib.escape(run.model))
        .replace("{{DURATION}}", _fmt_duration(run.duration_ms))
        .replace("{{NAV}}", nav_items)
        .replace("{{SECTIONS}}", body_sections)
        .replace("{{GENERATED_AT}}", generated_at)
    )


# --------------------------------------------------------------------------- #
# Self-contained HTML shell (no external CSS; one CDN script for Mermaid)
# --------------------------------------------------------------------------- #

_HTML_SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}} — Engineering Brief</title>
<style>
:root {
  --bg: #ffffff;
  --fg: #0f172a;
  --muted: #64748b;
  --border: #e2e8f0;
  --accent: #6366f1;
  --code-bg: #f8fafc;
  --card: #ffffff;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0b1020;
    --fg: #e2e8f0;
    --muted: #94a3b8;
    --border: #1e293b;
    --accent: #818cf8;
    --code-bg: #111a2e;
    --card: #111a2e;
  }
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
  background: var(--bg);
  color: var(--fg);
  line-height: 1.65;
}
.layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  max-width: 1280px;
  margin: 0 auto;
}
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  padding: 32px 24px;
  border-right: 1px solid var(--border);
  overflow-y: auto;
}
.brand {
  font-weight: 700;
  font-size: 13px;
  color: var(--accent);
  letter-spacing: 0.02em;
  margin-bottom: 4px;
}
.brand-sub {
  font-size: 11px;
  color: var(--muted);
  margin-bottom: 28px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.nav { display: flex; flex-direction: column; gap: 2px; }
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 6px;
  color: var(--fg);
  text-decoration: none;
  font-size: 13px;
  transition: background 0.15s, color 0.15s;
}
.nav-item:hover {
  background: var(--code-bg);
  color: var(--accent);
}
.nav-num {
  font-size: 10px;
  font-family: ui-monospace, monospace;
  color: var(--muted);
  font-weight: 600;
  min-width: 18px;
}
.nav-label { flex: 1; }
.main {
  padding: 56px 64px;
  max-width: 900px;
  min-width: 0;
}
.header {
  margin-bottom: 56px;
  padding-bottom: 28px;
  border-bottom: 1px solid var(--border);
}
.eyebrow {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 12px;
}
h1 {
  margin: 0 0 12px;
  font-size: 34px;
  letter-spacing: -0.02em;
  line-height: 1.15;
}
.idea {
  color: var(--muted);
  font-size: 16px;
  margin: 0 0 28px;
  line-height: 1.5;
}
.meta {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  font-size: 13px;
  color: var(--muted);
}
.meta strong {
  color: var(--fg);
  font-weight: 600;
  margin-right: 6px;
}
.badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.badge.completed, .badge.approve {
  background: rgba(16, 185, 129, 0.12);
  color: #047857;
  border: 1px solid rgba(16, 185, 129, 0.25);
}
@media (prefers-color-scheme: dark) {
  .badge.completed, .badge.approve { color: #6ee7b7; }
}
.badge.revise {
  background: rgba(245, 158, 11, 0.12);
  color: #92400e;
  border: 1px solid rgba(245, 158, 11, 0.25);
}
@media (prefers-color-scheme: dark) {
  .badge.revise { color: #fcd34d; }
}
.badge.failed, .badge.running, .badge.neutral {
  background: var(--code-bg);
  color: var(--muted);
  border: 1px solid var(--border);
}
.section {
  margin-top: 64px;
  scroll-margin-top: 24px;
}
.section-head { margin-bottom: 28px; }
.section-head h2 {
  margin: 0 0 8px;
  font-size: 24px;
  letter-spacing: -0.01em;
}
.section-meta {
  display: flex;
  gap: 12px;
  align-items: center;
}
.section-tag {
  font-size: 11px;
  font-weight: 600;
  color: var(--accent);
  background: rgba(99, 102, 241, 0.1);
  padding: 4px 10px;
  border-radius: 6px;
  letter-spacing: 0.02em;
}
.section-path {
  font-family: ui-monospace, monospace;
  font-size: 11px;
  color: var(--muted);
}
.section-body h1 { font-size: 26px; margin: 32px 0 12px; }
.section-body h2 {
  font-size: 20px;
  margin: 32px 0 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}
.section-body h3 { font-size: 16px; margin: 24px 0 8px; }
.section-body p { margin: 0 0 14px; }
.section-body ul, .section-body ol { margin: 0 0 18px; padding-left: 22px; }
.section-body li { margin-bottom: 4px; }
.section-body code {
  font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  font-size: 0.88em;
  background: var(--code-bg);
  padding: 1px 6px;
  border-radius: 4px;
  border: 1px solid var(--border);
}
.section-body pre {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px 20px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.5;
  margin: 14px 0 22px;
}
.section-body pre code {
  background: transparent;
  padding: 0;
  border: none;
  font-size: 13px;
}
.section-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0 22px;
  font-size: 14px;
}
.section-body th, .section-body td {
  text-align: left;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
}
.section-body th {
  font-weight: 600;
  background: var(--code-bg);
  font-size: 13px;
}
.section-body strong { color: var(--fg); font-weight: 600; }
.section-body blockquote {
  margin: 14px 0;
  padding: 10px 16px;
  border-left: 3px solid var(--accent);
  color: var(--muted);
  font-style: italic;
  background: var(--code-bg);
  border-radius: 0 6px 6px 0;
}
pre.mermaid {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 28px;
  text-align: center;
  margin: 18px 0 28px;
  font-family: inherit;
  overflow: visible;
}
.footer {
  margin-top: 96px;
  padding-top: 28px;
  border-top: 1px solid var(--border);
  font-size: 12px;
  color: var(--muted);
  text-align: center;
}
.print-hint {
  display: inline-block;
  margin-top: 16px;
  padding: 8px 14px;
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 12px;
  color: var(--muted);
}
.print-hint kbd {
  font-family: ui-monospace, monospace;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1px 6px;
  font-size: 11px;
}

@media print {
  .layout { grid-template-columns: 1fr; max-width: none; }
  .sidebar, .print-hint { display: none; }
  .main { padding: 0; max-width: none; }
  body { font-size: 11pt; }
  h1 { font-size: 24pt; }
  .section-body h2 { font-size: 14pt; page-break-after: avoid; }
  .section { page-break-inside: auto; margin-top: 32px; }
  pre, table { page-break-inside: avoid; }
}
@media (max-width: 880px) {
  .layout { grid-template-columns: 1fr; }
  .sidebar {
    position: relative;
    height: auto;
    border-right: none;
    border-bottom: 1px solid var(--border);
  }
  .main { padding: 32px 24px; }
  h1 { font-size: 26px; }
}
</style>
</head>
<body>
<div class="layout">
<aside class="sidebar">
<div class="brand">AI Engineering Team</div>
<div class="brand-sub">Engineering Brief</div>
<nav class="nav">{{NAV}}</nav>
</aside>
<main class="main">
<header class="header">
<div class="eyebrow">Engineering Brief</div>
<h1>{{TITLE}}</h1>
<p class="idea">{{IDEA}}</p>
<div class="meta">
<span><strong>Status:</strong><span class="badge {{STATUS_CLASS}}">{{STATUS}}</span></span>
<span><strong>Verdict:</strong><span class="badge {{VERDICT_CLASS}}">{{VERDICT}}</span></span>
<span><strong>Score:</strong>{{SCORE}}/100</span>
<span><strong>Iterations:</strong>{{ITERATIONS}}</span>
<span><strong>Model:</strong><code>{{MODEL}}</code></span>
<span><strong>Duration:</strong>{{DURATION}}</span>
</div>
<div class="print-hint">Tip: <kbd>Ctrl</kbd> + <kbd>P</kbd> to save as PDF</div>
</header>
{{SECTIONS}}
<footer class="footer">Generated by AI Engineering Team — {{GENERATED_AT}}</footer>
</main>
</div>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
if (window.mermaid) {
  mermaid.initialize({
    startOnLoad: true,
    theme: matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'default',
    securityLevel: 'loose'
  });
}
</script>
</body>
</html>
"""
