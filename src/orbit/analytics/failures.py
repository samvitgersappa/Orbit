from sqlalchemy import select

from orbit.database.models import FailureRecord, RunRecord, ToolCallRecord, TraceRecord
from orbit.database.session import AsyncSessionLocal


class FailureDetectionEngine:
    async def analyze_run(self, run_id: int):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(RunRecord).where(RunRecord.id == run_id))
            run = result.scalar_one_or_none()
            if not run:
                return

            tool_result = await session.execute(
                select(ToolCallRecord).where(ToolCallRecord.run_id == run_id)
            )
            tool_calls = tool_result.scalars().all()

            trace_result = await session.execute(
                select(TraceRecord).where(TraceRecord.run_id == run_id)
            )
            traces = trace_result.scalars().all()

            failures = []

            # 1. Tool Failure
            for tc in tool_calls:
                if not tc.success:
                    failures.append(
                        FailureRecord(
                            run_id=run_id,
                            failure_type="tool_failure",
                            root_cause=f"Tool '{tc.tool_name}' failed to execute properly.",
                            recommendation="Check tool input parameters or external tool availability.",
                        )
                    )

            # 2. Timeout
            if run.duration_ms and run.duration_ms > 60000:
                failures.append(
                    FailureRecord(
                        run_id=run_id,
                        failure_type="timeout",
                        root_cause="Run exceeded 60 seconds.",
                        recommendation="Optimize model prompt, switch to a smaller model, or check network latency.",
                    )
                )

            # 3. Empty Response
            if run.status == "failure" and not traces:
                failures.append(
                    FailureRecord(
                        run_id=run_id,
                        failure_type="empty_response",
                        root_cause="Agent failed before generating any traces.",
                        recommendation="Check the agent entrypoint and initialization logic.",
                    )
                )

            if failures:
                session.add_all(failures)
                await session.commit()
