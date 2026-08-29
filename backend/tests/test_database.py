from sqlalchemy import inspect

from app.database import engine


def test_database_engine_connects() -> None:
    """Database engine should be able to connect successfully."""
    with engine.connect() as connection:
        assert connection is not None


def test_database_tables_exist() -> None:
    """All application tables should exist after Alembic migration."""
    inspector = inspect(engine)

    tables = set(inspector.get_table_names())

    assert "tasks" in tables
    assert "runs" in tables
    assert "run_logs" in tables
    assert "eval_results" in tables
