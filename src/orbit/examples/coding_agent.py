"""Coding agent example: solves coding tasks and runs simple tests."""

from __future__ import annotations

import asyncio
import os
import time

from sqlalchemy import select

from orbit.database.models import RunRecord, ToolCallRecord, TraceRecord
from orbit.database.session import AsyncSessionLocal
from orbit.integrations.langgraph.trace import trace_agent
from orbit.integrations.ollama.client import OllamaClient
from orbit.security.guardrail import SecurityGuard


async def _get_latest_run_id() -> int:
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(RunRecord).order_by(RunRecord.id.desc()).limit(1))
        run = res.scalar_one_or_none()
        return run.id if run else 1


async def _record_trace(run_id: int, step: int, event_type: str, node: str, content: dict) -> None:
    async with AsyncSessionLocal() as session:
        trace = TraceRecord(
            run_id=run_id,
            step_number=step,
            event_type=event_type,
            node_name=node,
            content=content,
        )
        session.add(trace)
        await session.commit()


async def _record_tool(
    run_id: int, name: str, inp: dict, out: dict, success: bool, ms: int
) -> None:
    async with AsyncSessionLocal() as session:
        tc = ToolCallRecord(
            run_id=run_id,
            tool_name=name,
            tool_input=inp,
            tool_output=out,
            success=success,
            duration_ms=ms,
        )
        session.add(tc)
        await session.commit()


def _run_code_test(code: str) -> tuple[bool, str]:
    """Execute generated code in a sandboxed namespace and return (success, output)."""
    import io
    from contextlib import redirect_stdout

    namespace: dict = {}
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            exec(compile(code, "<generated>", "exec"), namespace)  # noqa: S102
        return True, buf.getvalue() or "OK"
    except Exception as exc:
        return False, str(exc)


@trace_agent(
    agent_name="coding_agent",
    task="Write a Python function for QuickSort",
    model_name=os.getenv("ORBIT_MODEL", "qwen3.5:4b"),
)
async def run_agent() -> dict:
    """Coding agent: generates code, tests it, and reports results."""
    client = OllamaClient()
    guard = SecurityGuard()
    step = 0

    run_id = await _get_latest_run_id()

    try:
        task = "Write a Python function for QuickSort."

        # --- Node 1: Security scan of prompt ---
        step += 1
        await _record_trace(run_id, step, "node_start", "prompt_guard", {"task": task})
        await guard.scan_input(run_id, task)
        await _record_trace(run_id, step, "node_end", "prompt_guard", {"safe": True})

        # --- Node 2: Code generation LLM call ---
        step += 1
        gen_prompt = (
            f"{task}\n\nProvide ONLY the Python function definition and a brief test call. "
            "No markdown, no explanation."
        )
        await _record_trace(
            run_id, step, "llm_call", "code_generator", {"prompt_length": len(gen_prompt)}
        )
        resp = await client.generate(os.getenv("ORBIT_MODEL", "qwen3.5:4b"), gen_prompt)
        code = resp.get("response", "")
        await guard.scan_output(run_id, code)
        await _record_trace(
            run_id, step, "node_end", "code_generator", {"code_preview": code[:300]}
        )

        # --- Node 3: Code execution tool ---
        step += 1
        await _record_trace(run_id, step, "node_start", "code_executor", {"code_length": len(code)})
        t0 = time.time()
        success, output = _run_code_test(code)
        exec_ms = int((time.time() - t0) * 1000)
        await _record_tool(
            run_id,
            "code_executor",
            {"code": code[:500]},
            {"output": output, "success": success},
            success,
            exec_ms,
        )
        await _record_trace(
            run_id, step, "node_end", "code_executor", {"success": success, "output": output}
        )

        # --- Node 4: Result reporting ---
        step += 1
        status = "✅ Passed" if success else "❌ Failed"
        await _record_trace(run_id, step, "node_end", "result_reporter", {"status": status})

        print(f"Coding Agent completed. Test result: {status}")
        print(f"Generated code preview:\n{code[:400]}")
        return {"code": code, "test_passed": success, "test_output": output}

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(run_agent())
