from pathlib import Path

ALLOWED_TEST_COMMANDS = {
    # Python
    "pytest",
    "pytest -q",
    "pytest -v",
    "pytest -q -x",
    "python -m pytest",
    "python -m pytest -q",
    "python -m pytest -v",
    "python -m pytest -q -x",
    # Go
    "go test ./...",
    "go test -v ./...",
    "go test ./... -count=1",
    "go test -v ./... -count=1",
    # Node / TypeScript / JavaScript
    "npm test",
    "npm run test",
    "npm test -- --runInBand",
    "npx vitest run",
    "npx jest --runInBand",
    # Rust
    "cargo test",
}

DEFAULT_TEST_COMMANDS = {
    "go": "go test ./...",
    "rust": "cargo test",
    "node": "npm test",
    "python": "pytest -q",
}


def validate_test_command(command: str) -> str:
    """Validate a test command before execution."""

    normalized = command.strip()

    if normalized not in ALLOWED_TEST_COMMANDS:
        raise ValueError(f"Unsupported test command: {command}")

    return normalized


def detect_language(files: list[str]) -> str:
    """
    Detect the dominant project language from repository files.

    Returns one of: go, rust, node, python.
    """

    names = {Path(file).name for file in files}

    if "go.mod" in names or any(file.endswith(".go") for file in files):
        return "go"

    if "Cargo.toml" in names or any(file.endswith(".rs") for file in files):
        return "rust"

    if "package.json" in names or any(
        file.endswith((".ts", ".tsx", ".js", ".jsx")) for file in files
    ):
        return "node"

    if (
        "pyproject.toml" in names
        or "requirements.txt" in names
        or any(file.endswith(".py") for file in files)
    ):
        return "python"

    return "python"


def resolve_test_command(command: str, repo_files: list[str]) -> str:
    """
    Return a safe test command for the project.

    The requested command is used if it is on the allowlist; otherwise a
    sensible default for the detected language is returned instead of
    crashing the run.
    """

    normalized = command.strip()

    if normalized in ALLOWED_TEST_COMMANDS:
        return normalized

    return DEFAULT_TEST_COMMANDS[detect_language(repo_files)]
