import typer
import asyncio
from typing import List
from orbit.arena.engine import ArenaEngine
import uvicorn
import subprocess

app = typer.Typer()

@app.command()
def trace(path: str):
    """Run and trace an agent script."""
    typer.echo(f"Tracing agent at {path}...")
    subprocess.run(["python", path])

@app.command()
def replay(run_id: int):
    """Display replay timeline in terminal."""
    typer.echo(f"Replaying run {run_id}...")

@app.command()
def battle(task: str, models: List[str]):
    """Run Agent Arena."""
    typer.echo(f"Running battle for task: '{task}' with models: {models}")
    engine = ArenaEngine()
    winner, details = asyncio.run(engine.run_battle(task, models))
    typer.echo(f"Winner: {winner}")
    typer.echo(f"Details: {details}")

@app.command()
def serve():
    """Start the ORBIT FastAPI backend."""
    typer.echo("Starting ORBIT...")
    uvicorn.run("orbit.backend.app:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    app()
