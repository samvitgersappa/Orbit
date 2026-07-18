import functools
import time
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from typing import Any

from orbit.analytics.ari import ARIEvaluator
from orbit.database.models import RunRecord
from orbit.database.session import AsyncSessionLocal


def trace_agent(agent_name: str, task: str, model_name: str):
    """
    Decorator to trace a LangGraph agent's execution.
    Creates a Run record and records start/end status.
    """

    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            async with AsyncSessionLocal() as session:
                new_run = RunRecord(
                    agent_name=agent_name, task=task, model_name=model_name, status="running"
                )
                session.add(new_run)
                await session.commit()
                await session.refresh(new_run)
                run_id = new_run.id

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)

                async with AsyncSessionLocal() as session:
                    run = await session.get(RunRecord, run_id)
                    if run:
                        run.status = "success"
                        run.success = True
                        run.finished_at = datetime.now(UTC)
                        run.duration_ms = int((time.time() - start_time) * 1000)
                    await session.commit()

                # In a full trace implementation, we would also extract
                # LangGraph callbacks and populate traces/tool_calls here.

                await ARIEvaluator().evaluate_run(run_id)
                return result
            except Exception as e:
                async with AsyncSessionLocal() as session:
                    run = await session.get(RunRecord, run_id)
                    if run:
                        run.status = "failure"
                        run.success = False
                        run.finished_at = datetime.now(UTC)
                        run.duration_ms = int((time.time() - start_time) * 1000)
                    await session.commit()
                await ARIEvaluator().evaluate_run(run_id)
                raise e

        return wrapper

    return decorator
