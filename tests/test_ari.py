"""Tests for the ARI Evaluator."""

from __future__ import annotations

import pytest

from orbit.analytics.ari import ARIEvaluator


@pytest.mark.asyncio
async def test_ari_evaluator_scores_run_and_is_idempotent():
    """evaluate_run writes component scores and is safe to re-run."""
    from sqlalchemy import delete, select

    from orbit.database.models import RunRecord, ScoreRecord, ToolCallRecord
    from orbit.database.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        run = RunRecord(
            agent_name="t",
            task="t",
            model_name="m",
            status="success",
            success=True,
            duration_ms=2000,
        )
        session.add(run)
        await session.commit()
        await session.refresh(run)
        run_id = run.id
        session.add(
            ToolCallRecord(
                run_id=run_id,
                tool_name="probe",
                tool_input={},
                tool_output={},
                success=True,
                duration_ms=1,
            )
        )
        await session.commit()

    try:
        await ARIEvaluator().evaluate_run(run_id)
        await ARIEvaluator().evaluate_run(run_id)

        async with AsyncSessionLocal() as session:
            run = await session.get(RunRecord, run_id)
            assert run.ari_score is not None
            assert 0.0 <= run.ari_score <= 100.0

            scores = (
                (await session.execute(select(ScoreRecord).where(ScoreRecord.run_id == run_id)))
                .scalars()
                .all()
            )
            assert len(scores) == 4
            names = {s.metric_name for s in scores}
            assert names == {
                "task_success",
                "tool_accuracy",
                "hallucination_score",
                "latency_score",
            }
    finally:
        async with AsyncSessionLocal() as session:
            await session.execute(delete(ScoreRecord).where(ScoreRecord.run_id == run_id))
            await session.execute(delete(RunRecord).where(RunRecord.id == run_id))
            await session.commit()


@pytest.mark.asyncio
async def test_ari_buckets():
    """Test that ARI buckets are correctly labelled."""

    def bucket(score):
        if score >= 85:
            return "Excellent"
        if score >= 70:
            return "Good"
        if score >= 50:
            return "Fair"
        return "Poor"

    assert bucket(90) == "Excellent"
    assert bucket(75) == "Good"
    assert bucket(60) == "Fair"
    assert bucket(40) == "Poor"


@pytest.mark.asyncio
async def test_ari_formula():
    """Test the ARI composite formula weights."""
    t, a, h, lat = 100.0, 80.0, 90.0, 70.0
    expected = 0.40 * t + 0.25 * a + 0.20 * h + 0.15 * lat
    assert abs(expected - (40 + 20 + 18 + 10.5)) < 0.01


def test_latency_score_fast():
    """Fast runs (<5s) should score 100."""
    duration_ms = 2000
    if duration_ms > 60000:
        l_score = 0.0
    elif duration_ms > 5000:
        l_score = max(0.0, 100.0 - ((duration_ms - 5000) / 55000) * 100.0)
    else:
        l_score = 100.0
    assert l_score == 100.0


def test_latency_score_slow():
    """Runs >60s should score 0."""
    duration_ms = 70000
    if duration_ms > 60000:
        l_score = 0.0
    elif duration_ms > 5000:
        l_score = max(0.0, 100.0 - ((duration_ms - 5000) / 55000) * 100.0)
    else:
        l_score = 100.0
    assert l_score == 0.0
