# ORBIT Architecture

## Overview

ORBIT is structured as a pipeline of loosely coupled modules, each responsible for a single concern. This document describes the data flow, module responsibilities, and design decisions.

## Data Flow

```
Agent Script
    │
    ▼
@trace_agent decorator (integrations/langgraph/trace.py)
    │
    ├──► SecurityGuard.scan_input()  ─► security_events DB
    │
    ├──► OllamaClient (integrations/ollama/client.py)
    │         │
    │         └──► Ollama (local HTTP, port 11434)
    │
    ├──► SecurityGuard.scan_output() ─► security_events DB
    │
    ├──► TraceRecord emission        ─► traces DB
    ├──► ToolCallRecord emission     ─► tool_calls DB
    │
    ▼
RunRecord saved (runs DB)
    │
    ├──► ARIEvaluator.evaluate_run() ─► scores DB, updates runs.ari_score
    └──► FailureDetectionEngine.analyze_run() ─► failures DB
                │
                ▼
        FastAPI backend (/runs, /metrics, /failures, /security/*, ...)
                │
                ▼
        React Dashboard  (localhost:5173)
```

## Module Responsibilities

### `integrations/langgraph/trace.py`
- `@trace_agent(agent_name, task, model_name)` decorator
- Creates a `RunRecord` at agent start
- Records `success`, `duration_ms`, `finished_at` at completion
- Agents call `_record_trace()` and `_record_tool()` internally for full observability

### `integrations/ollama/client.py`
- Async HTTP client wrapping the Ollama REST API
- Methods: `list_models()`, `generate()`, `chat()`, `health_check()`, `close()`

### `security/guardrail.py`
- Orchestrates `PromptInjectionDetector` and `LlamaGuard`
- `scan_input(run_id, text)` — checks before LLM call
- `scan_output(run_id, text)` — checks after LLM response
- Writes `SecurityEventRecord` rows with OWASP category mappings

### `security/injection.py`
- Wraps `little-canary` local injection detector
- Returns `(is_injection: bool, reason: str | None)`

### `security/ollama_guard.py`
- Async wrapper around Llama Guard 3 served via Ollama
- Returns `(is_unsafe: bool, categories: str | None)`

### `analytics/ari.py`
- `ARIEvaluator.evaluate_run(run_id)` — computes T/A/H/L scores
- Persists to `scores` table; updates `runs.ari_score`
- Formula: `ARI = 0.40*T + 0.25*A + 0.20*H + 0.15*L`

### `analytics/failures.py`
- `FailureDetectionEngine.analyze_run(run_id)` — post-run failure scan
- Detects: tool_failure, timeout, empty_response (Phase 1)
- Planned: hallucinated_tool, infinite_loop, low_confidence

### `replay/engine.py`
- `ReplayEngine.get_replay_steps(run_id)` — returns ordered trace steps
- Used by CLI `orbit replay` and dashboard Replay page

### `arena/engine.py`
- `ArenaEngine.run_battle(task, models)` — compares model ARI scores
- Persists `ArenaMatchRecord`; returns winner and per-model details

### `backend/api/__init__.py`
- FastAPI router with all spec endpoints
- Dependency injects `AsyncSessionLocal` and `OllamaClient`

### `cli/main.py`
- Typer app with all 9 spec commands
- `serve` wraps uvicorn; all others use `asyncio.run()` internally

## Database Schema

All persistence uses SQLAlchemy 2.0 async ORM with SQLite (via aiosqlite).

| Table | Purpose |
|---|---|
| `runs` | One row per agent execution |
| `traces` | Ordered execution events per run |
| `tool_calls` | Tool invocations with input/output/timing |
| `scores` | ARI component scores per run |
| `failures` | Detected failure patterns per run |
| `arena_matches` | Battle results with per-model details JSON |
| `security_events` | Security findings with OWASP mapping |
| `models` | Registered model metadata |
| `agents` | Registered agent metadata |

## Design Decisions

1. **Local-first**: No external API calls except to Ollama (localhost:11434). All data stays on device.
2. **Async throughout**: FastAPI + SQLAlchemy async + httpx — no blocking I/O.
3. **SQLite over PostgreSQL**: Zero-setup for local dev; spec explicitly targets single-machine use.
4. **Security Guard as middleware**: Every LLM call goes through `scan_input` / `scan_output` — not opt-in.
5. **Dependency injection via session factories**: `AsyncSessionLocal()` is used directly in handlers rather than FastAPI's `Depends()` to keep modules independently testable.
