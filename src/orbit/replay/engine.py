from sqlalchemy import select

from orbit.database.models import TraceRecord
from orbit.database.session import AsyncSessionLocal


class ReplayEngine:
    async def get_replay_steps(self, run_id: int):
        async with AsyncSessionLocal() as session:
            trace_result = await session.execute(select(TraceRecord).where(TraceRecord.run_id == run_id).order_by(TraceRecord.step_number))
            traces = trace_result.scalars().all()
            
            steps = []
            for t in traces:
                steps.append({
                    "id": t.id,
                    "type": t.event_type,
                    "node": t.node_name,
                    "content": t.content,
                    "timestamp": t.timestamp.isoformat()
                })
            return steps
