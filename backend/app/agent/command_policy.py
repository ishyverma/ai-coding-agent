ALLOWED_TEST_COMMANDS = {
    "pytest",
    "pytest -q",
    "pytest -v",
    "python -m pytest",
    "python -m pytest -q",
    "python -m pytest -v",
}


def validate_test_command(command: str) -> str:
    """Validate a test command before execution."""

    normalized = command.strip()

    if normalized not in ALLOWED_TEST_COMMANDS:
        raise ValueError(
            f"Unsupported test command: {command}"
        )

    return normalized