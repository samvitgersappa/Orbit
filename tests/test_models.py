"""Tests for the database models schema."""

from __future__ import annotations

from orbit.database.models import (
    ArenaMatchRecord,
    FailureRecord,
    RunRecord,
    ScoreRecord,
    SecurityEventRecord,
    ToolCallRecord,
    TraceRecord,
)


def test_run_record_tablename():
    assert RunRecord.__tablename__ == "runs"


def test_trace_record_tablename():
    assert TraceRecord.__tablename__ == "traces"


def test_tool_call_tablename():
    assert ToolCallRecord.__tablename__ == "tool_calls"


def test_score_tablename():
    assert ScoreRecord.__tablename__ == "scores"


def test_failure_tablename():
    assert FailureRecord.__tablename__ == "failures"


def test_arena_match_tablename():
    assert ArenaMatchRecord.__tablename__ == "arena_matches"


def test_security_event_tablename():
    assert SecurityEventRecord.__tablename__ == "security_events"


def test_run_record_has_ari_score():
    cols = [c.key for c in RunRecord.__table__.columns]
    assert "ari_score" in cols
    assert "status" in cols
    assert "duration_ms" in cols


def test_security_event_has_owasp():
    cols = [c.key for c in SecurityEventRecord.__table__.columns]
    assert "owasp_category" in cols
    assert "severity" in cols
    assert "detector" in cols
