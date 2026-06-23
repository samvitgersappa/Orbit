from fastapi import APIRouter
from orbit.database.models import RunRecord, FailureRecord
from orbit.database.session import AsyncSessionLocal
from sqlalchemy import select

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.get("/runs")
async def get_runs():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(RunRecord).order_by(RunRecord.started_at.desc()))
        runs = result.scalars().all()
        return [{"id": r.id, "agent_name": r.agent_name, "task": r.task, "status": r.status, "duration_ms": r.duration_ms, "ari_score": r.ari_score} for r in runs]

@router.get("/failures")
async def get_failures():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(FailureRecord).order_by(FailureRecord.created_at.desc()))
        failures = result.scalars().all()
        return [{"id": f.id, "run_id": f.run_id, "type": f.failure_type, "root_cause": f.root_cause, "recommendation": f.recommendation} for f in failures]
