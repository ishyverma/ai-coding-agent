import pytest

from app.agent.command_policy import validate_test_command


def test_pytest_command_is_allowed() -> None:
    assert validate_test_command("pytest -q") == "pytest -q"


def test_python_pytest_command_is_allowed() -> None:
    assert (
        validate_test_command("python -m pytest")
        == "python -m pytest"
    )


def test_unknown_command_is_rejected() -> None:
    with pytest.raises(ValueError):
        validate_test_command("rm -rf /")


def test_shell_chain_is_rejected() -> None:
    with pytest.raises(ValueError):
        validate_test_command(
            "pytest -q && rm -rf /"
        )