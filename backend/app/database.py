from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


def _create_engine():
    """Create the SQLAlchemy engine, adapting connect args to the dialect."""
    url = settings.database_url
    connect_args: dict = {}

    # check_same_thread is SQLite-specific; PostgreSQL does not use it.
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(url, connect_args=connect_args)


# Create the database engine
engine = _create_engine()

# Create a session factory
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# Base class for all SQLAlchemy models
class Base(DeclarativeBase):
    pass


# FastAPI dependency for getting a database session
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
