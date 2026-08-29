from pathlib import Path

from git import Repo

from app.agent.repository import (
    clone_repository,
    create_work_directory,
)


def test_clone_repository(tmp_path: Path) -> None:
    source_repo = tmp_path / "source"
    source_repo.mkdir()

    repo = Repo.init(source_repo)

    test_file = source_repo / "hello.txt"
    test_file.write_text("hello world")

    repo.index.add(["hello.txt"])
    repo.index.commit("initial commit")

    clone_dir = tmp_path / "clones"

    cloned_repo = clone_repository(
        str(source_repo),
        str(clone_dir),
    )

    assert cloned_repo.exists()
    assert cloned_repo.is_dir()

    cloned_file = cloned_repo / "hello.txt"

    assert cloned_file.exists()
    assert cloned_file.read_text() == "hello world"


def test_create_work_directory(tmp_path: Path) -> None:
    work_dir = create_work_directory(str(tmp_path))

    assert work_dir.exists()
    assert work_dir.is_dir()
    assert work_dir.parent == tmp_path


def test_work_directories_are_unique(tmp_path: Path) -> None:
    first = create_work_directory(str(tmp_path))
    second = create_work_directory(str(tmp_path))

    assert first != second
    assert first.exists()
    assert second.exists()
