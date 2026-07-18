# ORBIT Roadmap

## Phase 1 — Core Platform (Current ✅)

- ✅ Deep tracing via `@trace_agent` decorator (LangGraph)
- ✅ Ollama local model integration (async OllamaClient)
- ✅ SQLite persistence (SQLAlchemy 2.0 async)
- ✅ Agent Reliability Index (ARI) — T/A/H/L composite score
- ✅ Failure Detection Engine (tool_failure, timeout, empty_response)
- ✅ Failure Replay Engine (step-by-step timeline)
- ✅ Agent Arena (model vs model battle with leaderboard)
- ✅ Security Guard (Little Canary + Llama Guard 3, OWASP mapping)
- ✅ FastAPI backend with all 9 spec endpoints
- ✅ CLI — all 9 commands (serve, trace, replay, battle, report, runs, models, security, security-summary)
- ✅ React Dashboard — all 8 pages live (Overview, Runs, Failures, Arena, Replay, Models, Analytics, Security)
- ✅ Example agents: coding_agent, research_agent, retrieval_agent
- ✅ Docker (Dockerfile.backend, Dockerfile.frontend, docker-compose)
- ✅ CI/CD (GitHub Actions — lint, type-check, tests, frontend build)

## Phase 2 — Extensibility (Planned)

- [ ] Multi-framework support (CrewAI, AutoGen, Autogen Studio)
- [ ] Live replay mode (`orbit replay --live`) — step-through re-execution
- [ ] Advanced Arena: dedicated benchmark datasets, leaderboard persistence
- [ ] PII regex detector for security module
- [ ] OpenTelemetry export for integration with existing observability stacks
- [ ] Pluggable evaluator pipeline (custom ARI metric components)

## Phase 3 — Scale & Community (Future)

- [ ] Advanced benchmark suites for code generation and reasoning tasks
- [ ] Multi-user / auth for team deployment
- [ ] Advanced model-agnostic security policies
- [ ] ORBIT Cloud (opt-in hosted dashboard, zero-code setup)
- [ ] VS Code extension for inline trace visualization
- [ ] Notebook integration (Jupyter, Marimo)
