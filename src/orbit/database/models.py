from datetime import datetime, timezone
from typing import Optional, List, Any

from sqlalchemy import Integer, String, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class ModelRecord(Base):
    __tablename__ = "models"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    provider: Mapped[str] = mapped_column(String)
    quantization: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    parameters: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class AgentRecord(Base):
    __tablename__ = "agents"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    entrypoint: Mapped[str] = mapped_column(String)
    framework: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class RunRecord(Base):
    __tablename__ = "runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    agent_name: Mapped[str] = mapped_column(String)
    task: Mapped[str] = mapped_column(String)
    model_name: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    success: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ari_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    tool_calls: Mapped[List["ToolCallRecord"]] = relationship("ToolCallRecord", back_populates="run")
    traces: Mapped[List["TraceRecord"]] = relationship("TraceRecord", back_populates="run")
    scores: Mapped[List["ScoreRecord"]] = relationship("ScoreRecord", back_populates="run")
    failures: Mapped[List["FailureRecord"]] = relationship("FailureRecord", back_populates="run")
    security_events: Mapped[List["SecurityEventRecord"]] = relationship("SecurityEventRecord", back_populates="run")

class ToolCallRecord(Base):
    __tablename__ = "tool_calls"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    tool_name: Mapped[str] = mapped_column(String)
    tool_input: Mapped[Any] = mapped_column(JSON)
    tool_output: Mapped[Any] = mapped_column(JSON, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    success: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    
    run: Mapped["RunRecord"] = relationship("RunRecord", back_populates="tool_calls")

class TraceRecord(Base):
    __tablename__ = "traces"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    step_number: Mapped[int] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String)
    node_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    content: Mapped[Any] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    run: Mapped["RunRecord"] = relationship("RunRecord", back_populates="traces")

class ScoreRecord(Base):
    __tablename__ = "scores"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    metric_name: Mapped[str] = mapped_column(String)
    value: Mapped[float] = mapped_column(Float)

    run: Mapped["RunRecord"] = relationship("RunRecord", back_populates="scores")

class FailureRecord(Base):
    __tablename__ = "failures"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    failure_type: Mapped[str] = mapped_column(String)
    root_cause: Mapped[str] = mapped_column(String)
    recommendation: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    run: Mapped["RunRecord"] = relationship("RunRecord", back_populates="failures")

class ArenaMatchRecord(Base):
    __tablename__ = "arena_matches"
    id: Mapped[int] = mapped_column(primary_key=True)
    task: Mapped[str] = mapped_column(String)
    winner_model_name: Mapped[str] = mapped_column(String)
    details: Mapped[Any] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class SecurityEventRecord(Base):
    __tablename__ = "security_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    step_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    direction: Mapped[str] = mapped_column(String)
    detector: Mapped[str] = mapped_column(String)
    risk_type: Mapped[str] = mapped_column(String)
    owasp_category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    severity: Mapped[int] = mapped_column(Integer)
    details: Mapped[Any] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    run: Mapped["RunRecord"] = relationship("RunRecord", back_populates="security_events")
