from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from orbit.database.models import ArenaMatchRecord, RunRecord
from orbit.database.session import AsyncSessionLocal


class ArenaEngine:
    async def run_battle(self, task: str, models: list[str]):
        match_details: dict[str, dict[str, Any]] = {}
        winner = None
        best_ari = -1.0

        async with AsyncSessionLocal() as session:
            for model in models:
                stmt = (
                    select(RunRecord)
                    .where(RunRecord.task == task, RunRecord.model_name == model)
                    .order_by(RunRecord.started_at.desc())
                    .limit(1)
                )
                result = await session.execute(stmt)
                run = result.scalar_one_or_none()

                if run and run.ari_score is not None:
                    match_details[model] = {
                        "ari": run.ari_score,
                        "latency": run.duration_ms,
                        "success": run.success,
                    }
                    if run.ari_score > best_ari:
                        best_ari = run.ari_score
                        winner = model
                else:
                    match_details[model] = {"error": "No completed run found for this task."}

            if winner:
                match = ArenaMatchRecord(
                    task=task,
                    winner_model_name=winner,
                    details=match_details,
                    created_at=datetime.now(UTC),
                )
                session.add(match)
                await session.commit()

        return winner, match_details
