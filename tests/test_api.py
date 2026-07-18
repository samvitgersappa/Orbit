"""Tests for FastAPI API endpoints using async test client."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint():
    """GET /health should return status ok."""
    from orbit.backend.app import app
    from orbit.database.session import init_db

    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_runs_endpoint_returns_list():
    """GET /runs should return a list."""
    from orbit.backend.app import app
    from orbit.database.session import init_db

    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/runs")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_failures_endpoint_returns_list():
    """GET /failures should return a list."""
    from orbit.backend.app import app
    from orbit.database.session import init_db

    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/failures")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_metrics_endpoint_has_required_keys():
    """GET /metrics should have expected keys."""
    from orbit.backend.app import app
    from orbit.database.session import init_db

    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_runs" in data
    assert "success_rate" in data
    assert "ari_distribution" in data


@pytest.mark.asyncio
async def test_security_events_endpoint():
    """GET /security/events should return a list."""
    from orbit.backend.app import app
    from orbit.database.session import init_db

    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/security/events")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_security_summary_endpoint():
    """GET /security/summary should have expected keys."""
    from orbit.backend.app import app
    from orbit.database.session import init_db

    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/security/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_events" in data
    assert "by_owasp_category" in data


@pytest.mark.asyncio
async def test_run_not_found():
    """GET /runs/99999 should return 404."""
    from orbit.backend.app import app
    from orbit.database.session import init_db

    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/runs/99999")
    assert resp.status_code == 404
