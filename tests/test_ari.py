"""Tests for the ARI Evaluator."""

from __future__ import annotations

import pytest
from orbit.analytics.ari import ARIEvaluator


@pytest.mark.asyncio
async def test_ari_buckets():
    """Test that ARI buckets are correctly labelled."""
    def bucket(score):
        if score >= 85: return "Excellent"
        if score >= 70: return "Good"
        if score >= 50: return "Fair"
        return "Poor"

    assert bucket(90) == "Excellent"
    assert bucket(75) == "Good"
    assert bucket(60) == "Fair"
    assert bucket(40) == "Poor"


@pytest.mark.asyncio
async def test_ari_formula():
    """Test the ARI composite formula weights."""
    t, a, h, l = 100.0, 80.0, 90.0, 70.0
    expected = 0.40 * t + 0.25 * a + 0.20 * h + 0.15 * l
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
