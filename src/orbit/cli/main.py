"""Full Typer CLI implementing all spec commands."""

from __future__ import annotations

import asyncio
import subprocess
import sys
from typing import List, Optional

import typer
import uvicorn

app = typer.Typer(
    name="orbit",
    help="🪐 ORBIT – Local-first observability, replay, and security for LangGraph agents.",
    no_args_is_help=True,
)


# ---------------------------------------------------------------------------
# serve
# ---------------------------------------------------------------------------

@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to listen on"),
    reload: bool = typer.Option(True, help="Enable auto-reload"),
) -> None:
    """Start the ORBIT FastAPI backend server."""
    typer.echo("🪐 Starting ORBIT backend...")
    uvicorn.run("orbit.backend.app:app", host=host, port=port, reload=reload)


# ---------------------------------------------------------------------------
# trace
# ---------------------------------------------------------------------------

@app.command()
def trace(
    path: str = typer.Argument(..., help="Path to the agent script to trace"),
) -> None:
    """Run and trace an agent script."""
    typer.echo(f"🔍 Tracing agent at {path}...")
    result = subprocess.run([sys.executable, path], check=False)
    if result.returncode == 0:
        typer.echo("✅ Agent completed successfully.")
    else:
        typer.echo(f"❌ Agent exited with code {result.returncode}.", err=True)
        raise typer.Exit(result.returncode)


# ---------------------------------------------------------------------------
# replay
# ---------------------------------------------------------------------------

@app.command()
def replay(
    run_id: int = typer.Argument(..., help="Run ID to replay"),
) -> None:
    """Display step-by-step replay timeline for a run."""

    async def _replay() -> None:
        from orbit.replay.engine import ReplayEngine
        engine = ReplayEngine()
        steps = await engine.get_replay_steps(run_id)
        if not steps:
            typer.echo(f"⚠️  No trace steps found for run {run_id}.")
            return

        typer.echo(f"\n🔁 Replay for Run #{run_id}  ({len(steps)} steps)\n")
        typer.echo("─" * 60)
        for step in steps:
            ts = step.get("timestamp", "")[:19]
            node = step.get("node") or "—"
            ev_type = step.get("type", "")
            step_num = step.get("step", "?")
            typer.echo(f"  [{step_num:>3}] {ts}  {ev_type:<18} node={node}")
            content = step.get("content")
            if content:
                preview = str(content)[:120]
                typer.echo(f"        ↳ {preview}")
        typer.echo("─" * 60)

    asyncio.run(_replay())


# ---------------------------------------------------------------------------
# battle
# ---------------------------------------------------------------------------

@app.command()
def battle(
    task: str = typer.Option(..., help="Task description to evaluate"),
    models: List[str] = typer.Option(..., help="Models to pit against each other (repeat flag)"),
) -> None:
    """Run Agent Arena: compare multiple models on the same task."""

    async def _battle() -> None:
        from orbit.arena.engine import ArenaEngine
        typer.echo(f"\n🏟️  Agent Arena: {task!r}")
        typer.echo(f"   Models: {', '.join(models)}\n")
        engine = ArenaEngine()
        winner, details = await engine.run_battle(task, models)

        # Pretty table
        typer.echo(f"{'Model':<20} {'ARI':>6} {'Latency':>10} {'Success':>8}")
        typer.echo("─" * 48)
        for model, info in details.items():
            if "error" in info:
                typer.echo(f"{model:<20} {'N/A':>6} {'N/A':>10} {'error':>8}  ← {info['error']}")
            else:
                ari = f"{info.get('ari', 0):.1f}"
                lat = f"{info.get('latency', 0)} ms"
                suc = "✅" if info.get("success") else "❌"
                typer.echo(f"{model:<20} {ari:>6} {lat:>10} {suc:>8}")
        typer.echo("─" * 48)
        if winner:
            typer.echo(f"\n🏆 Winner: {winner}")
        else:
            typer.echo("\n⚠️  No winner determined — run the agents first to populate scores.")

    asyncio.run(_battle())


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

@app.command()
def report(
    run_id: int = typer.Argument(..., help="Run ID to report on"),
) -> None:
    """Print ARI breakdown, failures, and security summary for a run."""

    async def _report() -> None:
        from sqlalchemy import select

        from orbit.database.models import (
            FailureRecord,
            RunRecord,
            ScoreRecord,
            SecurityEventRecord,
        )
        from orbit.database.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            run = await session.get(RunRecord, run_id)
            if run is None:
                typer.echo(f"❌ Run {run_id} not found.", err=True)
                raise typer.Exit(1)

            scores_res = await session.execute(
                select(ScoreRecord).where(ScoreRecord.run_id == run_id)
            )
            scores = {s.metric_name: s.value for s in scores_res.scalars().all()}

            failures_res = await session.execute(
                select(FailureRecord).where(FailureRecord.run_id == run_id)
            )
            failures = failures_res.scalars().all()

            sec_res = await session.execute(
                select(SecurityEventRecord).where(SecurityEventRecord.run_id == run_id)
            )
            security_events = sec_res.scalars().all()

        status_icon = "✅" if run.success else "❌"
        typer.echo(f"\n📊 ORBIT Report — Run #{run_id}")
        typer.echo("═" * 50)
        typer.echo(f"  Agent    : {run.agent_name}")
        typer.echo(f"  Task     : {run.task}")
        typer.echo(f"  Model    : {run.model_name}")
        typer.echo(f"  Status   : {status_icon} {run.status}")
        typer.echo(f"  Duration : {run.duration_ms} ms" if run.duration_ms else "  Duration : —")
        typer.echo(f"\n  ARI Score: {run.ari_score:.1f}" if run.ari_score is not None else "\n  ARI Score: N/A")

        if scores:
            typer.echo("\n  ARI Components:")
            for name, value in scores.items():
                bar = "█" * int(value / 10) + "░" * (10 - int(value / 10))
                typer.echo(f"    {name:<25} {bar}  {value:.1f}")

        if failures:
            typer.echo(f"\n  ⚠️  Failures ({len(failures)}):")
            for f in failures:
                typer.echo(f"    [{f.failure_type}] {f.root_cause}")
                if f.recommendation:
                    typer.echo(f"      → {f.recommendation}")
        else:
            typer.echo("\n  ✅ No failures detected.")

        if security_events:
            typer.echo(f"\n  🛡️  Security Events ({len(security_events)}):")
            for se in security_events:
                typer.echo(f"    [{se.risk_type}] {se.owasp_category}  severity={se.severity}")
        else:
            typer.echo("\n  🛡️  No security events detected.")

        typer.echo("═" * 50)

    asyncio.run(_report())


# ---------------------------------------------------------------------------
# runs
# ---------------------------------------------------------------------------

@app.command()
def runs(
    limit: int = typer.Option(20, help="Number of recent runs to show"),
    status: Optional[str] = typer.Option(None, help="Filter by status: running|success|failure"),
) -> None:
    """List recent agent runs."""

    async def _runs() -> None:
        from sqlalchemy import select

        from orbit.database.models import RunRecord
        from orbit.database.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            stmt = select(RunRecord).order_by(RunRecord.started_at.desc()).limit(limit)
            if status:
                stmt = stmt.where(RunRecord.status == status)
            result = await session.execute(stmt)
            all_runs = result.scalars().all()

        if not all_runs:
            typer.echo("No runs found.")
            return

        typer.echo(f"\n{'ID':>5}  {'Agent':<20} {'Model':<15} {'Status':<10} {'ARI':>6}  {'Duration':>10}")
        typer.echo("─" * 72)
        for r in all_runs:
            ari = f"{r.ari_score:.1f}" if r.ari_score is not None else "—"
            dur = f"{r.duration_ms} ms" if r.duration_ms else "—"
            st = {"success": "✅ success", "failure": "❌ failure", "running": "⏳ running"}.get(r.status, r.status)
            typer.echo(f"{r.id:>5}  {r.agent_name:<20} {r.model_name:<15} {st:<10} {ari:>6}  {dur:>10}")

    asyncio.run(_runs())


# ---------------------------------------------------------------------------
# models
# ---------------------------------------------------------------------------

@app.command()
def models() -> None:
    """List available models from DB and live Ollama instance."""

    async def _models() -> None:
        from sqlalchemy import select

        from orbit.database.models import ModelRecord
        from orbit.database.session import AsyncSessionLocal
        from orbit.integrations.ollama.client import OllamaClient

        async with AsyncSessionLocal() as session:
            db_res = await session.execute(select(ModelRecord))
            db_models = db_res.scalars().all()

        client = OllamaClient()
        try:
            ollama_models = await client.list_models()
        except Exception as exc:
            ollama_models = []
            typer.echo(f"⚠️  Could not reach Ollama: {exc}", err=True)
        finally:
            await client.close()

        typer.echo("\n📦 Ollama Models (live):")
        if ollama_models:
            for m in ollama_models:
                name = m.get("name", "unknown")
                size = m.get("size", 0)
                size_gb = f"{size / 1e9:.1f} GB" if size else "—"
                typer.echo(f"  • {name:<30} {size_gb}")
        else:
            typer.echo("  (none — is Ollama running?)")

        typer.echo("\n🗄️  DB Models:")
        if db_models:
            for m in db_models:
                typer.echo(f"  • {m.name:<30} provider={m.provider}  quant={m.quantization or '—'}")
        else:
            typer.echo("  (none)")

    asyncio.run(_models())


# ---------------------------------------------------------------------------
# security
# ---------------------------------------------------------------------------

@app.command()
def security(
    run_id: int = typer.Argument(..., help="Run ID to inspect security events for"),
) -> None:
    """Show security events for a specific run."""

    async def _security() -> None:
        from sqlalchemy import select

        from orbit.database.models import SecurityEventRecord
        from orbit.database.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SecurityEventRecord)
                .where(SecurityEventRecord.run_id == run_id)
                .order_by(SecurityEventRecord.created_at)
            )
            events = result.scalars().all()

        if not events:
            typer.echo(f"✅ No security events for run {run_id}.")
            return

        typer.echo(f"\n🛡️  Security Events for Run #{run_id}  ({len(events)} total)\n")
        typer.echo(f"{'#':>4}  {'Direction':<10} {'Detector':<18} {'Risk Type':<22} {'OWASP':<30} {'Sev':>4}")
        typer.echo("─" * 92)
        for i, e in enumerate(events, 1):
            owasp = (e.owasp_category or "")[:28]
            typer.echo(
                f"{i:>4}  {e.direction:<10} {e.detector:<18} {e.risk_type:<22} {owasp:<30} {e.severity:>4}"
            )

    asyncio.run(_security())


# ---------------------------------------------------------------------------
# security-summary
# ---------------------------------------------------------------------------

@app.command(name="security-summary")
def security_summary() -> None:
    """Show aggregate OWASP-aligned security statistics."""

    async def _summary() -> None:
        from sqlalchemy import select

        from orbit.database.models import SecurityEventRecord
        from orbit.database.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(SecurityEventRecord))
            events = result.scalars().all()

        if not events:
            typer.echo("✅ No security events recorded yet.")
            return

        by_owasp: dict[str, int] = {}
        by_risk: dict[str, int] = {}
        affected: set[int] = set()
        for e in events:
            cat = e.owasp_category or "Unknown"
            by_owasp[cat] = by_owasp.get(cat, 0) + 1
            by_risk[e.risk_type] = by_risk.get(e.risk_type, 0) + 1
            affected.add(e.run_id)

        typer.echo(f"\n🛡️  Security Summary  —  {len(events)} total events, {len(affected)} affected runs\n")
        typer.echo("OWASP Categories:")
        for cat, count in sorted(by_owasp.items(), key=lambda x: -x[1]):
            bar = "█" * count
            typer.echo(f"  {cat:<40} {bar} {count}")
        typer.echo("\nRisk Types:")
        for risk, count in sorted(by_risk.items(), key=lambda x: -x[1]):
            typer.echo(f"  {risk:<30} {count}")

    asyncio.run(_summary())


if __name__ == "__main__":
    app()
