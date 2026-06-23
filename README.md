# ORBIT
> Observability for Runs, Behavior, Inspection, and Triage

ORBIT is an open-source developer tool designed to provide local-first observability, replay capabilities, and security guardrails for LangGraph agents running on Ollama. It enables developers to trace agent executions, understand failures, and ensure safety without relying on cloud infrastructure.

By operating entirely locally, ORBIT ensures that sensitive data, prompts, and agent internal states remain on your machine. It is optimized for Apple Silicon devices utilizing Ollama for inference and SQLite for data persistence.

---

## Key Features

- **Local-First Execution:** No telemetry, no cloud dependencies. Your data stays entirely on your device.
- **Deep Tracing:** Comprehensive tracing of LangGraph agents, capturing every node execution, tool call, and model response.
- **Failure Replay:** Reconstruct an agent's execution timeline step-by-step to visualize exactly where and why a failure occurred.
- **Agent Reliability Index (ARI):** A quantitative framework that scores agent runs based on task success, hallucination rates, tool accuracy, and latency.
- **Agent Arena:** Pit open-weights models against each other to evaluate performance across the same tasks objectively.
- **Security Guardrails:** Built-in prompt injection and toxic content filtering utilizing Little Canary and Llama Guard 3, categorized according to the OWASP Top 10 for LLMs.

---

## Architecture

ORBIT is composed of several specialized subsystems designed for high-performance local execution:

### 1. Tracing & Agent Integration
At its core, ORBIT provides the `@trace_agent` decorator which seamlessly instruments LangGraph applications. This module intercepts execution state, captures Ollama API interactions via a custom asynchronous client, and emits telemetry data to the local storage engine.

### 2. Security Guard
The Security module acts as a middleware for LLM interactions:
- **Input Scanning:** Utilizes the local `little-canary` library to detect obfuscated prompt injection attempts before they reach the primary inference model.
- **Content Safety:** Employs an asynchronous wrapper around Llama Guard 3 (served via Ollama) to analyze both user inputs and agent outputs for policy violations and toxicity.

### 3. Analytics & Evaluation Engines
- **Failure Detection Engine:** Post-processes execution traces to identify common failure patterns such as tool invocation errors, context window timeouts, or empty responses.
- **ARI Evaluator:** Computes the composite Agent Reliability Index by analyzing tool accuracy metrics and response latency.

### 4. Storage & API Layer
- **Database:** Uses `aiosqlite` and `SQLAlchemy 2.0` (async) to persist records (runs, traces, failures, arena matches) in a local SQLite database.
- **Backend:** A FastAPI application exposing asynchronous endpoints for the frontend dashboard and CLI.

### 5. Presentation Layer
- **Dashboard:** A Vite + React application styled with Tailwind CSS and shadcn/ui. It provides real-time insights into runs, security events, and agent comparisons.
- **CLI:** A Typer-based command-line interface for initiating traces, running arena battles, and launching the application server.

---

## Installation & Setup

### Prerequisites
- macOS on Apple Silicon (M-series) is recommended.
- Python 3.12+
- Node.js 20+
- [Ollama](https://ollama.com) installed and running locally.
- [uv](https://github.com/astral-sh/uv) package manager.

### Local Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/samvitgersappa/orbit.git
   cd orbit
   ```

2. **Sync dependencies:**
   ```bash
   uv sync
   ```

3. **Pull required Ollama models:**
   Ensure you have the required models for your agents and security guardrails.
   ```bash
   ollama pull llama3.1
   ollama pull llama-guard3
   ```

## Usage

### Starting the Server
Start the ORBIT FastAPI backend:
```bash
uv run orbit serve
```

*Note: In a separate terminal, ensure the React frontend is running via `npm run dev` in the `frontend` directory.*

### Tracing an Agent
Trace a provided example agent workflow:
```bash
uv run orbit trace src/orbit/examples/coding_agent.py
```

### Viewing the Dashboard
Navigate to `http://localhost:5173` to view the comprehensive ORBIT dashboard.

---

## Contribution Guide

We welcome contributions from the community to expand ORBIT's capabilities, add support for new agent frameworks, and improve the user experience.

### Development Environment Setup
1. Fork the repository and clone your fork locally.
2. Initialize the environment using `uv sync --all-extras --dev`.
3. Install frontend dependencies: `cd frontend && npm install`.

### Contribution Workflow
1. **Discuss before building:** For significant architectural changes or new features, please open an Issue to discuss your proposal with the maintainers.
2. **Branching:** Create a new branch for your feature or bug fix (`git checkout -b feature/your-feature-name`).
3. **Coding Standards:** 
   - Ensure all Python code is fully typed.
   - We use `ruff` for linting and formatting, and `mypy` for static type checking.
4. **Testing:** Write unit tests for your changes. Run the test suite via `uv run pytest` before submitting a pull request.
5. **Pull Requests:** Submit a clean, concise Pull Request. Ensure that the GitHub Actions CI pipeline passes successfully.

### Roadmap
Please consult the `docs/roadmap.md` file for an overview of planned features, including support for non-LangGraph frameworks (e.g., CrewAI, AutoGen) and advanced UI replay execution.

---

## License

ORBIT is distributed under the MIT License. See the `LICENSE` file for more information.
