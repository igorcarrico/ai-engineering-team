"""API-level test: create a project, run it to completion, read artifacts."""

from __future__ import annotations

import asyncio

import httpx
import pytest
from app.main import app
from httpx import ASGITransport


@pytest.fixture
async def client():
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


async def _wait_for_completion(client: httpx.AsyncClient, run_id: str, timeout: float = 15.0):
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        resp = await client.get(f"/api/runs/{run_id}")
        data = resp.json()
        if data["run"]["status"] in ("completed", "failed"):
            return data
        await asyncio.sleep(0.2)
    raise AssertionError("run did not finish in time")


async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_create_project_runs_to_completion(client):
    resp = await client.post(
        "/api/projects",
        json={"idea": "Build a SaaS platform for AI-powered financial analytics"},
    )
    assert resp.status_code == 201
    detail = resp.json()
    run_id = detail["run"]["id"]

    final = await _wait_for_completion(client, run_id)
    assert final["run"]["status"] == "completed"
    assert final["run"]["review_score"] is not None

    # Artifacts were produced and are retrievable.
    arts = (await client.get(f"/api/runs/{run_id}/artifacts")).json()
    assert len(arts) >= 7
    paths = {a["path"] for a in arts}
    assert "docs/00-delivery-summary.md" in paths

    # The workspace tree and exports work.
    tree = (await client.get(f"/api/runs/{run_id}/tree")).json()
    assert tree["total_files"] == len(arts)

    md = await client.get(f"/api/runs/{run_id}/export.md")
    assert md.status_code == 200
    assert "Feasibility Study" in md.text


async def test_list_projects(client):
    await client.post("/api/projects", json={"idea": "A habit tracking mobile app"})
    resp = await client.get("/api/projects")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1
