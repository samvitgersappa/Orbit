# Roadmap

## What's done (v0.1)

- `@trace_agent` decorator for LangGraph — records every node, LLM call, and tool invocation
- Ollama async client
- SQLite persistence via SQLAlchemy 2.0 async
- ARI scoring — task success, tool accuracy, hallucination, latency (weighted composite)
- Failure detection — tool_failure, timeout, empty_response
- Replay engine — CLI and dashboard
- Agent Arena — compare models on the same task, leaderboard persisted to DB
- Security Guard — Little Canary (injection) + Llama Guard 3 (content safety), OWASP tagging
- FastAPI backend with all the core endpoints
- CLI — serve, trace, replay, battle, report, runs, models, security, security-summary
- React dashboard — Overview, Runs, Failures, Arena, Replay, Models, Analytics, Security
- Three example agents (coding, research, retrieval)
- Docker setup
- GitHub Actions CI

## What's next

**More failure detectors** — hallucinated tool calls (model references a tool that wasn't invoked), infinite loops, low-confidence answers. The detection engine is easy to extend; it's just not been prioritised yet.

**PII detection** — there's a placeholder `pii.py` in the security module but it's not wired up. The plan is a regex-based scanner as a lightweight first pass.

**Live replay** — right now replay shows you what happened. The `--live` mode would actually re-execute each step, which is more useful for debugging but requires more work around state management.

**CrewAI / AutoGen** — the tracing decorator is LangGraph-specific. Supporting other frameworks means building different instrumentation hooks.

**OpenTelemetry export** — so ORBIT can feed into existing observability stacks if you want it to.

Nothing here is on a fixed timeline. If something on this list would be useful to you, open an issue.
