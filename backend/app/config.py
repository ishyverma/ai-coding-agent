from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    All app configuration.

    Values are read from the .env file automatically.
    If a required value is missing, the app fails at startup
    with a clear error.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # LLM
    groq_api_key: str

    # LangSmith
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "coding-agent"

    # Database
    database_url: str = "sqlite:///./dev.db"

    # App
    app_env: str = "development"
    secret_key: str = "dev-secret-change-in-production"

    # Agent Behaviour
    agent_max_attempts: int = 3
    agent_repo_work_dir: str = "/tmp/agent-repos"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

# Created one shared settings instance
settings = Settings()