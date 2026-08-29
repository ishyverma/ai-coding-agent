from app.config import settings


def test_settings_loads_without_error() -> None:
    """Settings class should load from .env without raising exceptions."""
    assert settings is not None


def test_settings_has_agent_max_attempts() -> None:
    assert settings.agent_max_attempts == 3


def test_is_production_returns_bool() -> None:
    assert isinstance(settings.is_production, bool)
