# ORBIT 🪐
> Observability for Runs, Behavior, Inspection, and Triage

ORBIT is an open-source developer tool that lets you **run any local AI agent and immediately understand why it succeeds, fails, or becomes unsafe**, entirely on your own machine.

It combines:
- **Deep tracing** of LangGraph agents
- **Failure replay** with timeline visualization
- A quantitative **Agent Reliability Index (ARI)**
- A model vs model **Agent Arena**
- A local **Security Guard** for prompt-injection & content-safety

Everything runs **fully offline** on a single Apple Silicon laptop using **Ollama** for models and **SQLite** for storage.

## Features
- 🚀 **Local First**: Your data never leaves your machine. SQLite powered.
- 🛡️ **Cybersecurity Guardrails**: Built-in prompt injection and toxic content filtering using Little Canary and Llama Guard 3.
- 📊 **Agent Reliability Index**: Automatically scores agent runs based on task success, hallucination rate, and execution latency.
- 🤺 **Model Arena**: Pit open-weights models against each other to evaluate performance objectively.

## Installation

Ensure you have [uv](https://github.com/astral-sh/uv) and [Ollama](https://ollama.com) installed.

```bash
git clone https://github.com/samvitgersappa/orbit.git
cd orbit
uv sync
```

## Quick Start

1. Start ORBIT backend and UI:
   ```bash
   uv run orbit serve
   ```
2. Trace an agent:
   ```bash
   uv run orbit trace src/orbit/examples/coding_agent.py
   ```
3. Open `http://localhost:5173` to view the dashboard.

## Contributing
Contributions are welcome! Please see the `docs/roadmap.md` for our current goals.
1. Open an issue for new feature ideas or bug reports.
2. For major changes, discuss via issue before opening a PR.
3. Ensure all tests pass locally (`pytest`), and linters (`ruff`, `mypy`) are clean.

## License
MIT License. See `LICENSE` for more information.
