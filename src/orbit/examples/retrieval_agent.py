"""Retrieval agent example: retrieval-augmented QA over local docs."""

from __future__ import annotations

import asyncio
import time

from orbit.database.models import RunRecord, ToolCallRecord, TraceRecord
from orbit.database.session import AsyncSessionLocal
from orbit.integrations.langgraph.trace import trace_agent
from orbit.integrations.ollama.client import OllamaClient
from orbit.security.guardrail import SecurityGuard
from sqlalchemy import select

# Simulated local document store
_LOCAL_DOCS = [
    {
        "id": "doc_1",
        "title": "Introduction to LangGraph",
        "content": "LangGraph is a library for building stateful, multi-actor applications with LLMs. "
                   "It models agent workflows as directed graphs where nodes are processing steps "
                   "and edges control flow between them.",
    },
    {
        "id": "doc_2",
        "title": "Ollama Local Inference",
        "content": "Ollama allows you to run large language models locally. It supports models like "
                   "Llama 3.1, Qwen 2.5, and Gemma 3. Models are downloaded once and run entirely "
                   "on your machine without any cloud dependencies.",
    },
    {
        "id": "doc_3",
        "title": "ORBIT Security Guard",
        "content": "ORBIT's Security Guard scans every LLM input and output. It uses Little Canary "
                   "for prompt injection detection and Llama Guard 3 for content safety classification "
                   "against the OWASP Top 10 for LLM Applications.",
    },
]


async def _get_latest_run_id() -> int:
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(RunRecord).order_by(RunRecord.id.desc()).limit(1))
        run = res.scalar_one_or_none()
        return run.id if run else 1


async def _record_trace(run_id: int, step: int, event_type: str, node: str, content: dict) -> None:
    async with AsyncSessionLocal() as session:
        trace = TraceRecord(
            run_id=run_id, step_number=step,
            event_type=event_type, node_name=node, content=content,
        )
        session.add(trace)
        await session.commit()


async def _record_tool(run_id: int, name: str, inp: dict, out: dict, success: bool, ms: int) -> None:
    async with AsyncSessionLocal() as session:
        tc = ToolCallRecord(
            run_id=run_id, tool_name=name,
            tool_input=inp, tool_output=out,
            success=success, duration_ms=ms,
        )
        session.add(tc)
        await session.commit()


def _retrieve(query: str, top_k: int = 2) -> list[dict]:
    """Simple keyword-based retrieval from local docs."""
    scored = []
    q_words = set(query.lower().split())
    for doc in _LOCAL_DOCS:
        doc_words = set((doc["title"] + " " + doc["content"]).lower().split())
        score = len(q_words & doc_words)
        scored.append((score, doc))
    scored.sort(key=lambda x: -x[0])
    return [doc for _, doc in scored[:top_k]]


@trace_agent(
    agent_name="retrieval_agent",
    task="Answer: How does ORBIT integrate with LangGraph and Ollama?",
    model_name="llama3.1",
)
async def run_agent() -> dict:
    """RAG agent: retrieves relevant local docs, then synthesizes an answer."""
    client = OllamaClient()
    guard = SecurityGuard()
    step = 0

    run_id = await _get_latest_run_id()

    try:
        question = "How does ORBIT integrate with LangGraph and Ollama?"

        # --- Node 1: Input validation ---
        step += 1
        await _record_trace(run_id, step, "node_start", "input_validator", {"question": question})
        await guard.scan_input(run_id, question)
        await _record_trace(run_id, step, "node_end", "input_validator", {"safe": True})

        # --- Node 2: Retrieval tool ---
        step += 1
        await _record_trace(run_id, step, "node_start", "retriever", {"query": question})
        t0 = time.time()
        docs = _retrieve(question)
        ret_ms = int((time.time() - t0) * 1000)
        await _record_tool(
            run_id, "local_retriever",
            {"query": question, "top_k": 2},
            {"docs": [d["id"] for d in docs], "count": len(docs)},
            True, ret_ms,
        )
        context = "\n\n".join(f"### {d['title']}\n{d['content']}" for d in docs)
        await _record_trace(run_id, step, "node_end", "retriever", {"retrieved_docs": len(docs)})

        # --- Node 3: Answer generation ---
        step += 1
        rag_prompt = (
            f"Use the following context to answer the question concisely.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\nAnswer:"
        )
        await _record_trace(run_id, step, "node_start", "answer_generator", {"context_length": len(context)})
        resp = await client.generate("llama3.1", rag_prompt)
        answer = resp.get("response", "")
        await guard.scan_output(run_id, answer)
        await _record_trace(run_id, step, "node_end", "answer_generator", {"answer_preview": answer[:300]})

        print("Retrieval Agent completed successfully.")
        print(f"Answer: {answer[:400]}")
        return {"answer": answer, "source_docs": [d["id"] for d in docs]}

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(run_agent())
