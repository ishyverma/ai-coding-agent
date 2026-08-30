from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import crud
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.api.tasks import router as tasks_router
from app.api.runs import router as runs_router
from app.api.evals import router as evals_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Runs during application startup and shutdown.
    """

    # Create database tables if not exist
    Base.metadata.create_all(bind=engine)
    _migrate_run_logs_diff()
    _mark_interrupted_runs_failed()

    print(f"Database tables created (env: {settings.app_env})")
    print(f"Agent work dir: {settings.agent_repo_work_dir}")

    yield


def _migrate_run_logs_diff() -> None:
    """Add the ``diff`` column to an existing ``run_logs`` table if missing."""

    with engine.connect() as connection:
        dialect = engine.dialect.name

        if dialect == "sqlite":
            columns = {
                row[1] for row in connection.exec_driver_sql("PRAGMA table_info(run_logs)")
            }
            if "diff" not in columns:
                connection.exec_driver_sql("ALTER TABLE run_logs ADD COLUMN diff TEXT")
                connection.commit()
        else:
            # PostgreSQL / other: use information_schema
            result = connection.exec_driver_sql(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'run_logs' AND column_name = 'diff'"
            )
            if result.fetchone() is None:
                connection.exec_driver_sql("ALTER TABLE run_logs ADD COLUMN diff TEXT")
                connection.commit()


def _mark_interrupted_runs_failed() -> None:
    """Recover process-local background work that cannot resume after restart."""

    db = SessionLocal()

    try:
        count = crud.mark_interrupted_runs_failed(db)

        if count:
            print(f"Marked {count} interrupted run(s) failed.")
    finally:
        db.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Coding Agent API",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Create tables and run lightweight migrations at import time so tests
    # and any process that skips the lifespan still get a working schema.
    Base.metadata.create_all(bind=engine)
    _migrate_run_logs_diff()
    _mark_interrupted_runs_failed()

    # Frontend will run on a different port during development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # All v1 API routes live under /api/v1/
    app.include_router(
        tasks_router,
        prefix="/api/v1",
    )

    app.include_router(
        runs_router,
        prefix="/api/v1",
    )

    app.include_router(
        evals_router,
        prefix="/api/v1",
    )

    @app.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        """
        Health check endpoint.

        Railway can use this endpoint to determine whether
        the application is alive.
        """

        return {"status": "ok", "version": "1.0.0", "env": settings.app_env}

    @app.post("/admin/clear-db", tags=["admin"])
    def clear_database() -> dict[str, str]:
        """Temporary endpoint to clear all data from the database."""
        from sqlalchemy import text

        tables = ["run_logs", "eval_results", "runs", "tasks"]
        with engine.connect() as conn:
            for table in tables:
                conn.execute(text(f"DELETE FROM {table}"))
            conn.commit()
        return {"status": "ok", "message": "All tables cleared"}

    return app


# Uvicorn needs this module level app instance
app = create_app()
