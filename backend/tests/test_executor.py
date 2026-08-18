from pathlib import Path

from app.agent.executor import run_command


def test_run_successful_command(tmp_path: Path) -> None:
    result = run_command(
        repo_path=str(tmp_path),
        command="python -c \"print('hello')\"",
    )

    assert result.passed is True
    assert result.return_code == 0
    assert "hello" in result.stdout
    assert result.timed_out is False


def test_run_failing_command(tmp_path: Path) -> None:
    result = run_command(
        repo_path=str(tmp_path),
        command="python -c \"print('failure'); raise SystemExit(1)\"",
    )

    assert result.passed is False
    assert result.return_code == 1
    assert "failure" in result.stdout
    assert result.timed_out is False


def test_run_command_captures_stderr(tmp_path: Path) -> None:
    result = run_command(
        repo_path=str(tmp_path),
        command=(
            "python -c "
            "\"import sys; "
            "print('error message', file=sys.stderr)\""
        ),
    )

    assert result.passed is True
    assert "error message" in result.stderr


def test_run_command_timeout(tmp_path: Path) -> None:
    result = run_command(
        repo_path=str(tmp_path),
        command=(
            "python -c "
            "\"import time; time.sleep(2)\""
        ),
        timeout=1,
    )

    assert result.passed is False
    assert result.timed_out is True
    assert result.return_code == -1


def test_invalid_repository_path(tmp_path: Path) -> None:
    missing_path = tmp_path / "does-not-exist"

    try:
        run_command(
            repo_path=str(missing_path),
            command="echo hello",
        )
    except FileNotFoundError:
        pass
    else:
        raise AssertionError(
            "Expected FileNotFoundError"
        )


def test_run_pytest_inside_repository(
    tmp_path: Path,
) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()

    test_file = tests_dir / "test_example.py"

    test_file.write_text(
        """
def test_example():
    assert 1 + 1 == 2
"""
    )

    result = run_command(
        repo_path=str(tmp_path),
        command="pytest -q",
    )

    assert result.passed is True
    assert "1 passed" in result.stdout