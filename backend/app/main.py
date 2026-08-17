from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import v1_router
from app.config import settings
from app.database import Base, engine
from app import models

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Runs during application startup and shutdown.
    """

    # Create database tables if not exist
    Base.metadata.create_all(bind=engine)

    print(f"Database tables created (env: {settings.app_env})")
    print(f"Agent work dir: {settings.agent_repo_work_dir}")

    yield

def create_app() -> FastAPI:
    app = FastAPI(
        title="Coding Agent API",
        version="1.0.0",
        lifespan=lifespan,
    )

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
        v1_router,
        prefix="/api/v1",
    )

    @app.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        """
        Health check endpoint.

        Railway can use this endpoint to determine whether
        the application is alive.
        """

        return {
            "status": "ok",
            "version": "1.0.0",
            "env": settings.app_env
        }
    
    return app

# Uvicorn needs this module level app instance
app = create_app()