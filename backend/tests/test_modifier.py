from pathlib import Path

import pytest

from app.agent.modifier import (
    UnsafeFilePathError,
    apply_file_change,
    apply_file_changes,
    validate_file_path,
)


def test_validate_file_path_accepts_valid_path(
    tmp_path: Path,
) -> None:
    path = validate_file_path(
        str(tmp_path),
        "src/main.py",
    )

    assert path == tmp_path / "src" / "main.py"


def test_validate_file_path_rejects_path_traversal(
    tmp_path: Path,
) -> None:
    with pytest.raises(UnsafeFilePathError):
        validate_file_path(
            str(tmp_path),
            "../../outside.txt",
        )


def test_apply_file_change(
    tmp_path: Path,
) -> None:
    target = apply_file_change(
        repo_path=str(tmp_path),
        file_path="src/main.py",
        content="print('hello')",
    )

    assert target.exists()
    assert target.read_text(encoding="utf-8") == "print('hello')"


def test_apply_multiple_file_changes(
    tmp_path: Path,
) -> None:
    changes = [
        {
            "path": "src/main.py",
            "content": "print('hello')",
        },
        {
            "path": "tests/test_main.py",
            "content": "def test_main(): pass",
        },
    ]

    modified_files = apply_file_changes(
        repo_path=str(tmp_path),
        changes=changes,
    )

    assert len(modified_files) == 2

    assert (tmp_path / "src" / "main.py").read_text(
        encoding="utf-8"
    ) == "print('hello')"

    assert (tmp_path / "tests" / "test_main.py").read_text(
        encoding="utf-8"
    ) == "def test_main(): pass"
