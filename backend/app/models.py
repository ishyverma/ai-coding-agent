from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import now

from app.database import Base

class Task(Base):
    """A coding task submitted by the user."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    repo_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    task_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=func.now(),
    )

    # One task can have multiple runs
    runs: Mapped[list["Run"]] = relationship(
        "Run",
        back_populates="task",
        cascade="all, delete-orphan",
    )

class Run(Base):
    """One attempt to complete a task. A task can have many runs."""

    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Status lifecycle: running -> passed | failed | gave_up
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="running",
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    tokens_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    duration_s: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    error_msg: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=func.now(),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="runs",
    )

    logs: Mapped[list["RunLog"]] = relationship(
        "RunLog",
        back_populates="run",
        cascade="all, delete-orphan",
    )

class RunLog(Base):
    """One log entry from the agent during a run. Many logs per run."""

    __tablename__ = "run_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Which agent node generated this log
    step: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    level: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="info",
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=func.now(),
    )

    run: Mapped["Run"] = relationship(
        "Run",
        back_populates="logs",
    )


class EvalResult(Base):
    """Aggregate result from running the eval suite."""

    __tablename__ = "eval_results"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    eval_name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    total_tasks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    passed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    failed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    pass_rate: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    avg_attempts: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    avg_tokens: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    avg_duration_s: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    run_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=func.now(),
    )
