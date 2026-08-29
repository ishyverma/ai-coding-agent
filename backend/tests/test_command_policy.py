import pytest

from app.agent.command_policy import (
    detect_language,
    resolve_test_command,
    validate_test_command,
)


def test_pytest_command_is_allowed() -> None:
    assert validate_test_command("pytest -q") == "pytest -q"


def test_python_pytest_command_is_allowed() -> None:
    assert validate_test_command("python -m pytest") == "python -m pytest"


def test_go_test_command_is_allowed() -> None:
    assert validate_test_command("go test ./...") == "go test ./..."


def test_npm_test_command_is_allowed() -> None:
    assert validate_test_command("npm test") == "npm test"


def test_cargo_test_command_is_allowed() -> None:
    assert validate_test_command("cargo test") == "cargo test"


def test_unknown_command_is_rejected() -> None:
    with pytest.raises(ValueError):
        validate_test_command("rm -rf /")


def test_shell_chain_is_rejected() -> None:
    with pytest.raises(ValueError):
        validate_test_command("pytest -q && rm -rf /")


def test_detect_language_go() -> None:
    assert detect_language(["go.mod", "cmd/main.go"]) == "go"


def test_detect_language_rust() -> None:
    assert detect_language(["Cargo.toml", "src/lib.rs"]) == "rust"


def test_detect_language_node() -> None:
    assert detect_language(["package.json", "src/index.ts"]) == "node"


def test_detect_language_python() -> None:
    assert detect_language(["pyproject.toml", "src/app.py"]) == "python"


def test_resolve_test_command_uses_allowed_command() -> None:
    assert (
        resolve_test_command("go test ./...", ["go.mod", "main.go"]) == "go test ./..."
    )


def test_resolve_test_command_falls_back_by_language() -> None:
    """An unsupported command must fall back, never crash the run."""

    assert resolve_test_command("make test", ["go.mod", "main.go"]) == "go test ./..."

    assert resolve_test_command("mvn test", ["package.json", "src/a.ts"]) == "npm test"

    assert (
        resolve_test_command("make check", ["Cargo.toml", "src/lib.rs"]) == "cargo test"
    )

    assert (
        resolve_test_command("make check", ["src/app.py", "requirements.txt"])
        == "pytest -q"
    )
