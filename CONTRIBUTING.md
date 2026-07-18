# Contributing

Thanks for looking at ORBIT. Here's everything you need to get set up and submit changes.

---

## Getting started

Fork the repo, then:

```bash
git clone https://github.com/<your-username>/Orbit.git
cd Orbit
git remote add upstream https://github.com/samvitgersappa/Orbit.git
```

---

## Dev setup

You need Python 3.12+, Node.js 20+, and [uv](https://github.com/astral-sh/uv).

```bash
# install Python deps
uv sync

# install frontend deps
cd frontend && npm install && cd ..

# run the backend
uv run orbit serve

# run the frontend (separate terminal)
cd frontend && npm run dev
```

Tests:

```bash
uv run pytest
uv run ruff check src/
uv run mypy src/
```

---

## Project layout

```
orbit/
├── src/orbit/
│   ├── analytics/      # ARI scoring and failure detection
│   ├── arena/          # arena battle engine
│   ├── backend/        # FastAPI app and routes
│   ├── cli/            # Typer CLI commands
│   ├── database/       # SQLAlchemy models and session
│   ├── examples/       # example LangGraph agents
│   ├── integrations/   # LangGraph decorator, Ollama client
│   ├── replay/         # replay engine
│   └── security/       # injection detection, content safety
├── frontend/           # React + TypeScript dashboard
├── tests/              # pytest test suite
├── docs/               # architecture and roadmap
└── docker/             # Dockerfiles
```

---

## Code style

**Python:**
- type hints everywhere
- `async`/`await` for all I/O — no sync DB or HTTP calls
- `ruff` for formatting and linting, `mypy` for type checking
- docstrings on public functions

**TypeScript:**
- functional components with hooks
- existing shadcn/ui components rather than raw HTML
- follow the Tailwind patterns already in the file

---

## Making changes

Work on a branch:

```bash
git checkout -b your-feature-name
```

Commit messages — just write what you did, no prefix required:

```
add /runs/{id} endpoint
fix missing model fallback in arena engine
improve latency scoring for sub-second runs
```

Before opening a PR, make sure `ruff`, `mypy`, and `pytest` all pass.

For anything significant — a new feature, a refactor, a change to the data model — open an issue first. Easier to align before writing a lot of code.

---

## Things that still need doing

- **More failure detectors** — hallucinated tool calls, infinite loops, low-confidence answers (currently only tool_failure, timeout, and empty_response are implemented)
- **PII detection** — the security module has a placeholder for a regex-based PII scanner
- **Live replay** — re-executing individual steps in the dashboard rather than just reviewing past trace data
- **CrewAI / AutoGen** — the `@trace_agent` decorator currently only wraps LangGraph graphs
- **More test coverage** — the existing tests cover the API and models; the analytics and security engines need more unit tests

---

## Bugs and feature requests

Use the issue templates — they just ask for the basics. If something's broken, include the full error output and your Ollama version.

---

## Code of Conduct

Be decent to people. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
