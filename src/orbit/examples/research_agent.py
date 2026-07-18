"""Research agent example: multi-step research workflow instrumented with ORBIT."""

from __future__ import annotations

import asyncio

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


async def _record_tool_call(run_id: int, name: str, inp: dict, out: dict, success: bool, ms: int) -> None:
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


@trace_agent(
    agent_name="research_agent",
    task="Research the latest trends in large language model quantization",
    model_name="llama3.1",
)
async def run_agent() -> dict:
    """Multi-step research workflow that queries Ollama and synthesizes findings."""
    client = OllamaClient()
    guard = SecurityGuard()
    step = 0

    run_id = await _get_latest_run_id()

    try:
        # --- Node 1: Query formulation ---
        step += 1
        await _record_trace(run_id, step, "node_start", "query_formulator", {})

        query = "What are the latest techniques and trends in LLM quantization (GPTQ, AWQ, GGUF)?"
        await guard.scan_input(run_id, query)

        response = await client.generate("llama3.1", query)
        answer = response.get("response", "")
        await guard.scan_output(run_id, answer)

        await _record_trace(
            run_id, step, "node_end", "query_formulator",
            {"query": query, "response_preview": answer[:200]}
        )

        # --- Node 2: Tool — web_search (simulated) ---
        step += 1
        import time

        await _record_trace(run_id, step, "node_start", "web_search", {"query": query})
        t0 = time.time()
        # Simulate tool execution with a follow-up prompt
        search_response = await client.generate(
            "llama3.1",
            f"Pretend you searched the web for: '{query}'. Summarise 3 key findings in bullet points.",
        )
        search_ms = int((time.time() - t0) * 1000)
        search_result = search_response.get("response", "")
        await _record_tool_call(
            run_id, "web_search",
            {"query": query},
            {"results": search_result[:500]},
            True, search_ms,
        )
        await _record_trace(run_id, step, "node_end", "web_search", {"results_preview": search_result[:200]})

        # --- Node 3: Synthesis ---
        step += 1
        synth_prompt = f"Based on these research findings:\n{search_result}\n\nWrite a concise 2-paragraph executive summary."
        await _record_trace(run_id, step, "node_start", "synthesizer", {"input_length": len(search_result)})

        synth_response = await client.generate("llama3.1", synth_prompt)
        summary = synth_response.get("response", "")
        await guard.scan_output(run_id, summary)

        await _record_trace(run_id, step, "node_end", "synthesizer", {"summary": summary[:400]})

        print("Research Agent completed successfully.")
        print(f"Summary preview: {summary[:300]}")
        return {"summary": summary, "steps": step}

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(run_agent())
