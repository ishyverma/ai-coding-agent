from unittest.mock import MagicMock, patch

from app.agent.llm import (
    TokenUsage,
    ask_llm,
    generate_code_change_plan,
    _record_usage,
    track_tokens,
)
from app.agent.schemas import CodeChangePlan


def test_ask_llm_returns_response_content() -> None:
    mock_response = MagicMock()
    mock_response.content = "LLM connection successful"

    with patch("app.agent.llm.create_llm") as mock_create_llm:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_response

        mock_create_llm.return_value = mock_llm

        result = ask_llm("Say hello")

    assert result == "LLM connection successful"
    mock_llm.invoke.assert_called_once_with("Say hello")


def test_track_tokens_accumulates_usage() -> None:
    usage = TokenUsage()

    mock_response = MagicMock()
    mock_response.usage_metadata = {"total_tokens": 42}

    with track_tokens(usage):
        _record_usage(mock_response)
        _record_usage(mock_response)

    assert usage.total == 84


def test_track_tokens_ignores_missing_metadata() -> None:
    usage = TokenUsage()

    mock_response = MagicMock()
    mock_response.usage_metadata = None

    with track_tokens(usage):
        _record_usage(mock_response)

    assert usage.total == 0


def test_track_tokens_resets_between_blocks() -> None:
    first = TokenUsage()
    second = TokenUsage()

    mock_response = MagicMock()
    mock_response.usage_metadata = {"total_tokens": 10}

    with track_tokens(first):
        _record_usage(mock_response)

    with track_tokens(second):
        _record_usage(mock_response)

    assert first.total == 10
    assert second.total == 10


def test_ask_llm_records_token_usage() -> None:
    usage = TokenUsage()

    mock_response = MagicMock()
    mock_response.content = "Analysis"
    mock_response.usage_metadata = {"total_tokens": 77}

    with patch("app.agent.llm.create_llm") as mock_create_llm:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_response

        mock_create_llm.return_value = mock_llm

        with track_tokens(usage):
            ask_llm("Analyze this")

    assert usage.total == 77


def test_generate_code_change_plan_returns_plan_on_first_try() -> None:
    plan = CodeChangePlan(
        changes=[],
        test_command="pytest -q",
    )

    with patch("app.agent.llm.create_structured_llm") as mock_create:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = plan

        mock_create.return_value = mock_llm

        result = generate_code_change_plan("Fix the bug")

    assert result is plan
    mock_llm.invoke.assert_called_once()


def test_generate_code_change_plan_retries_on_provider_error() -> None:
    """A Groq 400 (no tool call / bad schema) must not crash the run."""

    plan = CodeChangePlan(
        changes=[],
        test_command="go test ./...",
    )

    with patch("app.agent.llm.create_structured_llm") as mock_create:
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = [
            RuntimeError("Tool choice is required, but model did not call a tool"),
            plan,
        ]

        mock_create.return_value = mock_llm

        result = generate_code_change_plan("Fix the bug")

    assert result is plan
    assert mock_llm.invoke.call_count == 2


def test_generate_code_change_plan_gives_up_after_max_retries() -> None:
    with patch("app.agent.llm.create_structured_llm") as mock_create:
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = RuntimeError("provider down")

        mock_create.return_value = mock_llm

        try:
            generate_code_change_plan("Fix the bug", max_retries=3)
        except RuntimeError as exc:
            assert "provider down" in str(exc)
        else:
            raise AssertionError("expected RuntimeError")

    assert mock_llm.invoke.call_count == 3
