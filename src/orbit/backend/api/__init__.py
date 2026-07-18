"""Full FastAPI router implementing all spec endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from orbit.database.models import (
    ArenaMatchRecord,
    FailureRecord,
    ModelRecord,
    RunRecord,
    ScoreRecord,
    SecurityEventRecord,
    ToolCallRecord,
    TraceRecord,
)
from orbit.database.session import AsyncSessionLocal
from orbit.integrations.ollama.client import OllamaClient

router = APIRouter()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Return service health and Ollama connectivity."""
    client = OllamaClient()
    ollama_ok = await client.health_check()
    await client.close()
    return {"status": "ok", "ollama": ollama_ok, "timestamp": datetime.now(UTC).isoformat()}


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------

@router.get("/runs")
async def get_runs() -> list[dict[str, Any]]:
    """List all runs ordered by most recent."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(RunRecord).order_by(RunRecord.started_at.desc())
        )
        runs = result.scalars().all()
        return [
            {
                "id": r.id,
                "agent_name": r.agent_name,
                "task": r.task,
                "model_name": r.model_name,
                "status": r.status,
                "success": r.success,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                "duration_ms": r.duration_ms,
                "ari_score": r.ari_score,
            }
            for r in runs
        ]


@router.get("/runs/{run_id}")
async def get_run(run_id: int) -> dict[str, Any]:
    """Get detailed info for a single run including traces, scores, failures, and security events."""
    async with AsyncSessionLocal() as session:
        run = await session.get(RunRecord, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")

        traces_res = await session.execute(
            select(TraceRecord).where(TraceRecord.run_id == run_id).order_by(TraceRecord.step_number)
        )
        traces = traces_res.scalars().all()

        tools_res = await session.execute(
            select(ToolCallRecord).where(ToolCallRecord.run_id == run_id)
        )
        tools = tools_res.scalars().all()

        scores_res = await session.execute(
            select(ScoreRecord).where(ScoreRecord.run_id == run_id)
        )
        scores = scores_res.scalars().all()

        failures_res = await session.execute(
            select(FailureRecord).where(FailureRecord.run_id == run_id)
        )
        failures = failures_res.scalars().all()

        security_res = await session.execute(
            select(SecurityEventRecord).where(SecurityEventRecord.run_id == run_id)
        )
        security_events = security_res.scalars().all()

        return {
            "id": run.id,
            "agent_name": run.agent_name,
            "task": run.task,
            "model_name": run.model_name,
            "status": run.status,
            "success": run.success,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "duration_ms": run.duration_ms,
            "ari_score": run.ari_score,
            "traces": [
                {
                    "id": t.id,
                    "step_number": t.step_number,
                    "event_type": t.event_type,
                    "node_name": t.node_name,
                    "content": t.content,
                    "timestamp": t.timestamp.isoformat(),
                }
                for t in traces
            ],
            "tool_calls": [
                {
                    "id": tc.id,
                    "tool_name": tc.tool_name,
                    "tool_input": tc.tool_input,
                    "tool_output": tc.tool_output,
                    "duration_ms": tc.duration_ms,
                    "success": tc.success,
                }
                for tc in tools
            ],
            "scores": [{"metric_name": s.metric_name, "value": s.value} for s in scores],
            "failures": [
                {
                    "id": f.id,
                    "failure_type": f.failure_type,
                    "root_cause": f.root_cause,
                    "recommendation": f.recommendation,
                }
                for f in failures
            ],
            "security_events": [
                {
                    "id": se.id,
                    "direction": se.direction,
                    "detector": se.detector,
                    "risk_type": se.risk_type,
                    "owasp_category": se.owasp_category,
                    "severity": se.severity,
                    "details": se.details,
                }
                for se in security_events
            ],
        }


@router.get("/runs/{run_id}/replay")
async def get_run_replay(run_id: int) -> dict[str, Any]:
    """Return ordered replay steps for a run."""
    async with AsyncSessionLocal() as session:
        run = await session.get(RunRecord, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")

        traces_res = await session.execute(
            select(TraceRecord)
            .where(TraceRecord.run_id == run_id)
            .order_by(TraceRecord.step_number)
        )
        traces = traces_res.scalars().all()

        tools_res = await session.execute(
            select(ToolCallRecord).where(ToolCallRecord.run_id == run_id)
        )
        tools = tools_res.scalars().all()

        steps = [
            {
                "step": t.step_number,
                "type": t.event_type,
                "node": t.node_name,
                "content": t.content,
                "timestamp": t.timestamp.isoformat(),
            }
            for t in traces
        ]

        return {
            "run_id": run_id,
            "agent_name": run.agent_name,
            "task": run.task,
            "model_name": run.model_name,
            "status": run.status,
            "duration_ms": run.duration_ms,
            "steps": steps,
            "tool_calls": [
                {
                    "tool_name": tc.tool_name,
                    "tool_input": tc.tool_input,
                    "tool_output": tc.tool_output,
                    "duration_ms": tc.duration_ms,
                    "success": tc.success,
                }
                for tc in tools
            ],
        }


# ---------------------------------------------------------------------------
# Failures
# ---------------------------------------------------------------------------

@router.get("/failures")
async def get_failures() -> list[dict[str, Any]]:
    """List all detected failures ordered by most recent."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(FailureRecord).order_by(FailureRecord.created_at.desc())
        )
        failures = result.scalars().all()
        return [
            {
                "id": f.id,
                "run_id": f.run_id,
                "type": f.failure_type,
                "root_cause": f.root_cause,
                "recommendation": f.recommendation,
                "created_at": f.created_at.isoformat(),
            }
            for f in failures
        ]


# ---------------------------------------------------------------------------
# Arena
# ---------------------------------------------------------------------------

@router.get("/arena")
async def get_arena() -> dict[str, Any]:
    """Return arena matches and model leaderboard."""
    async with AsyncSessionLocal() as session:
        matches_res = await session.execute(
            select(ArenaMatchRecord).order_by(ArenaMatchRecord.created_at.desc())
        )
        matches = matches_res.scalars().all()

        # Build leaderboard: aggregate wins and avg ARI per model
        leaderboard: dict[str, dict[str, Any]] = {}
        for m in matches:
            winner = m.winner_model_name
            if winner not in leaderboard:
                leaderboard[winner] = {"model": winner, "wins": 0, "matches": 0}
            leaderboard[winner]["wins"] += 1

            if isinstance(m.details, dict):
                for model_name, details in m.details.items():
                    if model_name not in leaderboard:
                        leaderboard[model_name] = {"model": model_name, "wins": 0, "matches": 0, "avg_ari": 0.0}
                    leaderboard[model_name]["matches"] += 1
                    if isinstance(details, dict) and "ari" in details:
                        prev = leaderboard[model_name].get("avg_ari", 0.0)
                        count = leaderboard[model_name]["matches"]
                        leaderboard[model_name]["avg_ari"] = (prev * (count - 1) + details["ari"]) / count

        return {
            "matches": [
                {
                    "id": m.id,
                    "task": m.task,
                    "winner": m.winner_model_name,
                    "details": m.details,
                    "created_at": m.created_at.isoformat(),
                }
                for m in matches
            ],
            "leaderboard": sorted(leaderboard.values(), key=lambda x: x.get("wins", 0), reverse=True),
        }


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@router.get("/models")
async def get_models() -> dict[str, Any]:
    """List models from DB and live Ollama instance."""
    async with AsyncSessionLocal() as session:
        db_res = await session.execute(select(ModelRecord))
        db_models = db_res.scalars().all()

    client = OllamaClient()
    try:
        ollama_models = await client.list_models()
    except Exception:
        ollama_models = []
    finally:
        await client.close()

    return {
        "db_models": [
            {
                "id": m.id,
                "name": m.name,
                "provider": m.provider,
                "quantization": m.quantization,
                "parameters": m.parameters,
            }
            for m in db_models
        ],
        "ollama_models": ollama_models,
    }


# ---------------------------------------------------------------------------
# Metrics / Analytics
# ---------------------------------------------------------------------------

@router.get("/metrics")
async def get_metrics() -> dict[str, Any]:
    """Return aggregated ARI, success rates, and reliability metrics."""
    async with AsyncSessionLocal() as session:
        total_res = await session.execute(select(func.count()).select_from(RunRecord))
        total = total_res.scalar() or 0

        success_res = await session.execute(
            select(func.count()).select_from(RunRecord).where(RunRecord.success == True)  # noqa: E712
        )
        successes = success_res.scalar() or 0

        avg_ari_res = await session.execute(
            select(func.avg(RunRecord.ari_score)).where(RunRecord.ari_score != None)  # noqa: E711
        )
        avg_ari = avg_ari_res.scalar()

        avg_latency_res = await session.execute(
            select(func.avg(RunRecord.duration_ms)).where(RunRecord.duration_ms != None)  # noqa: E711
        )
        avg_latency = avg_latency_res.scalar()

        failures_res = await session.execute(select(func.count()).select_from(FailureRecord))
        total_failures = failures_res.scalar() or 0

        security_res = await session.execute(select(func.count()).select_from(SecurityEventRecord))
        total_security = security_res.scalar() or 0

        # ARI distribution buckets
        excellent_res = await session.execute(
            select(func.count()).select_from(RunRecord).where(RunRecord.ari_score >= 85)
        )
        good_res = await session.execute(
            select(func.count()).select_from(RunRecord).where(
                RunRecord.ari_score >= 70, RunRecord.ari_score < 85
            )
        )
        fair_res = await session.execute(
            select(func.count()).select_from(RunRecord).where(
                RunRecord.ari_score >= 50, RunRecord.ari_score < 70
            )
        )
        poor_res = await session.execute(
            select(func.count()).select_from(RunRecord).where(RunRecord.ari_score < 50)
        )

        return {
            "total_runs": total,
            "successful_runs": successes,
            "failed_runs": total - successes,
            "success_rate": round(successes / total * 100, 1) if total else 0.0,
            "average_ari": round(float(avg_ari), 2) if avg_ari else None,
            "average_latency_ms": round(float(avg_latency), 1) if avg_latency else None,
            "total_failures": total_failures,
            "total_security_events": total_security,
            "ari_distribution": {
                "excellent": excellent_res.scalar() or 0,
                "good": good_res.scalar() or 0,
                "fair": fair_res.scalar() or 0,
                "poor": poor_res.scalar() or 0,
            },
        }


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

@router.get("/security/events")
async def get_security_events() -> list[dict[str, Any]]:
    """List all security events ordered by most recent."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(SecurityEventRecord).order_by(SecurityEventRecord.created_at.desc())
        )
        events = result.scalars().all()
        return [
            {
                "id": e.id,
                "run_id": e.run_id,
                "step_number": e.step_number,
                "direction": e.direction,
                "detector": e.detector,
                "risk_type": e.risk_type,
                "owasp_category": e.owasp_category,
                "severity": e.severity,
                "details": e.details,
                "created_at": e.created_at.isoformat(),
            }
            for e in events
        ]


@router.get("/security/summary")
async def get_security_summary() -> dict[str, Any]:
    """Return aggregate security stats grouped by OWASP category."""
    async with AsyncSessionLocal() as session:
        total_res = await session.execute(select(func.count()).select_from(SecurityEventRecord))
        total = total_res.scalar() or 0

        events_res = await session.execute(select(SecurityEventRecord))
        events = events_res.scalars().all()

        by_owasp: dict[str, int] = {}
        by_risk_type: dict[str, int] = {}
        by_detector: dict[str, int] = {}
        affected_runs: set[int] = set()

        for e in events:
            cat = e.owasp_category or "Unknown"
            by_owasp[cat] = by_owasp.get(cat, 0) + 1
            by_risk_type[e.risk_type] = by_risk_type.get(e.risk_type, 0) + 1
            by_detector[e.detector] = by_detector.get(e.detector, 0) + 1
            affected_runs.add(e.run_id)

        return {
            "total_events": total,
            "affected_runs": len(affected_runs),
            "by_owasp_category": by_owasp,
            "by_risk_type": by_risk_type,
            "by_detector": by_detector,
        }
