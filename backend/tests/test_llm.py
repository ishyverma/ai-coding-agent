from unittest.mock import MagicMock, patch

from app.agent.llm import ask_llm


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