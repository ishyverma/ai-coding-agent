from sqlalchemy import inspect

from app.database import Base, engine


def test_database_engine_connects() -> None:
    """Database engine should be able to connect successfully."""
    with engine.connect() as connection:
        assert connection is not None


def test_base_has_no_tables_yet() -> None:
    """No models have been defined yet."""
    inspector = inspect(engine)
    assert inspector.get_table_names() == []