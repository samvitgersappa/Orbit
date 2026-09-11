# Architecture

## How it fits together

When you run an agent with `@trace_agent`, here's what happens:

```
Agent script
    │
    ▼
@trace_agent decorator
    │
    ├── RunRecord                  →  writes to runs (start / end status)
    │
    ├── ARIEvaluator.evaluate_run() →  scores table, updates ari_score
    │
    └── FailureDetectionEngine      →  failures table
                │
                ▼
        FastAPI backend
                │
                ▼
        React dashboard (localhost:5173)
```

Example agents also call `SecurityGuard.scan_input()` / `scan_output()`
explicitly on each LLM interaction:

```
Agent script
    │
    ├── SecurityGuard.scan_input()  →  writes to security_events
    │         ├── Little Canary (injection) via orbit/security/injection.py
    │         └── Llama Guard 3 (content safety) via orbit/security/ollama_guard.py
    │
    └── SecurityGuard.scan_output() →  writes to security_events
```

---

## Modules

**`integrations/langgraph/trace.py`** — the `@trace_agent` decorator. Creates a run record at start, closes it with success/failure status at the end, then runs the ARI evaluator and the failure detection engine. Agents call `_record_trace()` and `_record_tool()` directly to emit events during execution.

**`integrations/ollama/client.py`** — thin async HTTP wrapper around the Ollama API. Covers `list_models`, `generate`, `chat`, `health_check`. Uses an explicit long read timeout (default 120s) so slow generations don't trip httpx's default 5s limit.

**`security/guardrail.py`** — the `SecurityGuard`. Calls the injection detector and Llama Guard in sequence for every LLM input (and Llama Guard for output). Writes `SecurityEventRecord` rows. Detection rows carry an OWASP category tag; screening failures (detector unavailable / degraded / error) are recorded separately as `screening_degraded` with no OWASP tag so they never count as findings.

**`security/injection.py`** — wraps Little Canary's `SecurityPipeline` in advisory mode, running the sync library call off the event loop. `scan()` returns `(bool, reason)`; `scan_detailed()` adds a `status` of `ok` / `degraded` / `unavailable` / `error` so a canary that could not run is never recorded as a clean scan.

**`security/ollama_guard.py`** — calls Llama Guard 3 via Ollama's generate API, parses the safe/unsafe response. A failed call (Ollama unreachable, model missing) returns a `LLAMA_GUARD_ERROR_PREFIX` message so the guardrail records it as degraded rather than clean.

**`analytics/ari.py`** — computes the ARI after a run completes. Formula: `ARI = 0.40*T + 0.25*A + 0.20*H + 0.15*L`. Writes to the `scores` table and updates `runs.ari_score`.

**`analytics/failures.py`** — post-run pass over traces and tool calls looking for known failure patterns. Currently catches tool_failure, timeout, and empty_response. More detectors are planned. Wired into the run lifecycle in `trace.py`; re-running is idempotent.

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
| `security_events` | injection/content findings with OWASP category, plus `screening_degraded` availability records (no OWASP tag) |
| `models` | registered model metadata |
| `agents` | registered agent metadata |

---

## A few design choices worth noting

**Everything local.** The only external HTTP call is to Ollama at `localhost:11434`. No analytics, no telemetry, nothing leaves the machine.

**Async throughout.** FastAPI, SQLAlchemy, and httpx are all async. Avoids blocking the event loop on DB queries or model calls.

**SQLite not Postgres.** Zero setup, zero config, works everywhere. The trade-off (no concurrent writes under load) doesn't matter for a single-user local tool.

**Security scanning is always on.** The example agents call `scan_input` and `scan_output` on every LLM interaction. If Little Canary or Llama Guard can't run, the failure is recorded as a `screening_degraded` event (severity 3, no OWASP tag) and the run continues — it is never mistaken for a clean scan. The dashboard's "Security Alerts" count reflects actual findings only, so a missing optional dependency doesn't look like a security incident.

**No FastAPI Depends() for the DB session.** `AsyncSessionLocal()` is called directly in each handler. It's a bit repetitive but makes the modules independently testable without needing to wire up FastAPI's dependency injection.
