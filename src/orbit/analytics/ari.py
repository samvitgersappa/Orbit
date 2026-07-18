from sqlalchemy import select

from orbit.database.models import RunRecord, ScoreRecord, ToolCallRecord
from orbit.database.session import AsyncSessionLocal


class ARIEvaluator:
    async def evaluate_run(self, run_id: int):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(RunRecord).where(RunRecord.id == run_id))
            run = result.scalar_one_or_none()
            if not run:
                return

            tool_result = await session.execute(select(ToolCallRecord).where(ToolCallRecord.run_id == run_id))
            tool_calls = tool_result.scalars().all()

            # 1. Task Success (T)
            t_score = 100.0 if run.success else 0.0

            # 2. Tool Accuracy (A)
            a_score = 100.0
            if tool_calls:
                success_count = sum(1 for tc in tool_calls if tc.success)
                a_score = (success_count / len(tool_calls)) * 100.0

            # 3. Hallucination Score (H)
            h_score = 100.0  # Simple default for phase 1

            # 4. Latency Score (L)
            l_score = 100.0
            if run.duration_ms:
                if run.duration_ms > 60000:
                    l_score = 0.0
                elif run.duration_ms > 5000:
                    l_score = max(0.0, 100.0 - ((run.duration_ms - 5000) / 55000) * 100.0)

            # Composite ARI
            ari = (0.40 * t_score) + (0.25 * a_score) + (0.20 * h_score) + (0.15 * l_score)

            scores = [
                ScoreRecord(run_id=run_id, metric_name="task_success", value=t_score),
                ScoreRecord(run_id=run_id, metric_name="tool_accuracy", value=a_score),
                ScoreRecord(run_id=run_id, metric_name="hallucination_score", value=h_score),
                ScoreRecord(run_id=run_id, metric_name="latency_score", value=l_score)
            ]
            
            run.ari_score = ari
            session.add_all(scores)
            await session.commit()
