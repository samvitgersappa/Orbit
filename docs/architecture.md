# Architecture

## How it fits together

When you run an agent with `@trace_agent`, here's what happens:

```
Agent script
    │
    ▼
@trace_agent decorator
    │
    ├── SecurityGuard.scan_input()   →  writes to security_events
    │
    ├── OllamaClient                 →  talks to Ollama at localhost:11434
    │
    ├── SecurityGuard.scan_output()  →  writes to security_events
    │
    ├── TraceRecord                  →  writes to traces
    ├── ToolCallRecord               →  writes to tool_calls
    │
    ▼
RunRecord (runs table)
    │
    ├── ARIEvaluator.evaluate_run()  →  scores table, updates ari_score
    └── FailureDetectionEngine       →  failures table
                │
                ▼
        FastAPI backend
                │
                ▼
        React dashboard (localhost:5173)
```

---

## Modules

**`integrations/langgraph/trace.py`** — the `@trace_agent` decorator. Creates a run record at start, closes it with success/failure status at the end. Agents call `_record_trace()` and `_record_tool()` directly to emit events during execution.

**`integrations/ollama/client.py`** — thin async HTTP wrapper around the Ollama API. Covers `list_models`, `generate`, `chat`, `health_check`.

**`security/guardrail.py`** — calls the injection detector and Llama Guard in sequence for every LLM call (both input and output). Writes `SecurityEventRecord` rows with OWASP category tags.

**`security/injection.py`** — wraps Little Canary, returns `(bool, reason)`.

**`security/ollama_guard.py`** — calls Llama Guard 3 via Ollama's generate API, parses the safe/unsafe response.

**`analytics/ari.py`** — computes the ARI after a run completes. Formula: `ARI = 0.40*T + 0.25*A + 0.20*H + 0.15*L`. Writes to the `scores` table and updates `runs.ari_score`.

**`analytics/failures.py`** — post-run pass over traces and tool calls looking for known failure patterns. Currently catches tool_failure, timeout, and empty_response. More detectors are planned.

**`replay/engine.py`** — reads `traces` for a given run in step order. Used by both the CLI `orbit replay` command and the dashboard.

**`arena/engine.py`** — looks up the most recent run for each model on a given task, compares ARI scores, picks a winner, writes an `ArenaMatchRecord`.

**`backend/api/__init__.py`** — single FastAPI router with all the API endpoints. No service layer abstraction currently; handlers call `AsyncSessionLocal` directly.

**`cli/main.py`** — Typer app. Each command either calls uvicorn (serve) or wraps an async function with `asyncio.run()`.

---

## Database

SQLAlchemy 2.0 async ORM, SQLite via aiosqlite. One file (`orbit.db` by default, configurable via `ORBIT_DB_PATH`).

| Table | What's in it |
|---|---|
| `runs` | one row per agent execution |
| `traces` | ordered events within a run (node starts/ends, LLM calls) |
| `tool_calls` | tool invocations with input, output, timing, success flag |
| `scores` | ARI component scores (task_success, tool_accuracy, etc.) |
| `failures` | detected failure patterns with root cause and recommendation |
| `arena_matches` | battle results with per-model metrics as JSON |
| `security_events` | injection/content findings with OWASP category |
| `models` | registered model metadata |
| `agents` | registered agent metadata |

---

## A few design choices worth noting

**Everything local.** The only external HTTP call is to Ollama at `localhost:11434`. No analytics, no telemetry, nothing leaves the machine.

**Async throughout.** FastAPI, SQLAlchemy, and httpx are all async. Avoids blocking the event loop on DB queries or model calls.

**SQLite not Postgres.** Zero setup, zero config, works everywhere. The trade-off (no concurrent writes under load) doesn't matter for a single-user local tool.

**Security scanning is always on.** `scan_input` and `scan_output` are called on every LLM interaction in the trace decorator — not opt-in per call. If Llama Guard or Little Canary isn't available, the errors are caught and the run continues.

**No FastAPI Depends() for the DB session.** `AsyncSessionLocal()` is called directly in each handler. It's a bit repetitive but makes the modules independently testable without needing to wire up FastAPI's dependency injection.
