from app.database import Base
from app.models import EvalResult, Run, RunLog, Task


def test_all_models_are_registered() -> None:
    """All four SQLAlchemy models should be registered with Base."""
    table_names = set(Base.metadata.tables.keys())

    assert "tasks" in table_names
    assert "runs" in table_names
    assert "run_logs" in table_names
    assert "eval_results" in table_names


def test_model_relationships_exist() -> None:
    """Task → Run → RunLog relationships should exist."""
    assert hasattr(Task, "runs")
    assert hasattr(Run, "task")
    assert hasattr(Run, "logs")
    assert hasattr(RunLog, "run")


def test_model_primary_keys_exist() -> None:
    """Every model should have an id primary key."""
    assert Task.__table__.c.id.primary_key
    assert Run.__table__.c.id.primary_key
    assert RunLog.__table__.c.id.primary_key
    assert EvalResult.__table__.c.id.primary_key