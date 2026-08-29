from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# Create the database engine
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})

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
