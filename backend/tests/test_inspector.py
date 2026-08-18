from pathlib import Path

from app.agent.inspector import (
    detect_file_extensions,
    find_important_files,
    find_test_files,
    list_repository_files,
)


def create_test_repository(tmp_path: Path) -> Path:
    """Create a small fake repository for testing."""

    repo = tmp_path / "repo"

    (repo / "src").mkdir(parents=True)
    (repo / "tests").mkdir(parents=True)
    (repo / ".git" / "objects").mkdir(parents=True)
    (repo / "node_modules" / "package").mkdir(parents=True)

    (repo / "src" / "main.py").write_text(
        "print('hello')"
    )

    (repo / "src" / "utils.py").write_text(
        "def add(a, b): return a + b"
    )

    (repo / "tests" / "test_main.py").write_text(
        "def test_main(): pass"
    )

    (repo / "README.md").write_text(
        "# Test Repository"
    )

    (repo / "requirements.txt").write_text(
        "pytest"
    )

    (repo / ".git" / "objects" / "fake").write_text(
        "should be ignored"
    )

    (repo / "node_modules" / "package" / "fake.js").write_text(
        "should be ignored"
    )

    return repo


def test_list_repository_files(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)

    files = list_repository_files(str(repo))

    assert "src/main.py" in files
    assert "src/utils.py" in files
    assert "tests/test_main.py" in files
    assert "README.md" in files

    assert ".git/objects/fake" not in files
    assert "node_modules/package/fake.js" not in files


def test_find_test_files(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)

    test_files = find_test_files(str(repo))

    assert "tests/test_main.py" in test_files


def test_find_important_files(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)

    important_files = find_important_files(str(repo))

    assert "README.md" in important_files
    assert "requirements.txt" in important_files


def test_detect_file_extensions(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)

    extensions = detect_file_extensions(str(repo))

    assert extensions[".py"] == 3