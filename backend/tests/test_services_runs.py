from pathlib import Path
from unittest.mock import patch

import pytest
from git import Repo
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import crud
from app.database import Base
from app.schemas import TaskCreate
from app.services.runs import _execute_run


TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
)


class FakeGraph:
    """Minimal stand-in for the LangGraph agent."""

    def __init__(self, updates: list[dict]) -> None:
        self.updates = updates
        self.raise_error: Exception | None = None

    def stream(self, state, stream_mode="updates"):
        if self.raise_error is not None:
            raise self.raise_error

        for update in self.updates:
            yield update


@pytest.fixture
def db():
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def source_repo(tmp_path: Path) -> Path:
    """A local git repo the service can clone."""

    repo = tmp_path / "source"
    repo.mkdir()

    git_repo = Repo.init(repo)
    (repo / "calc.py").write_text("def add(a, b):\n    return a * b\n")
    git_repo.index.add(["calc.py"])
    git_repo.index.commit("initial")

    return repo


def _create_task_and_run(db):
    task = crud.create_task(
        db,
        TaskCreate(
            repo_url="https://github.com/example/repo",
            task_text="Fix the add function",
        ),
    )
    run = crud.create_run(db, task.id)
    return task, run


def test_execute_run_marks_run_passed(
    db,
    source_repo: Path,
    tmp_path: Path,
) -> None:
    task, run = _create_task_and_run(db)

    fake_graph = FakeGraph(
        updates=[
            {
                "setup": {"repo_path": str(source_repo)},
            },
            {
                "inspect": {
                    "repository_files": ["calc.py"],
                    "test_files": [],
                },
            },
            {
                "run_tests": {
                    "test_output": "1 passed",
                    "tests_passed": True,
                    "attempt_count": 1,
                },
            },
        ]
    )

    clone_dir = tmp_path / "work"

    with (
        patch(
            "app.services.runs.build_agent_graph",
            return_value=fake_graph,
        ),
        patch(
            "app.services.runs.clone_repository",
            return_value=clone_dir,
        ),
    ):
        clone_dir.mkdir()
        _execute_run(
            db,
            task_id=task.id,
            run_id=run.id,
            repo_url=str(source_repo),
            task_text="Fix the add function",
        )

    db.refresh(run)
    db.refresh(task)

    assert run.status == "passed"
    assert run.attempts == 1
    assert run.completed_at is not None
    assert task.status == "done"

    logs = crud.get_run_logs(db, run.id)

    steps = [log.step for log in logs]

    assert "setup" in steps
    assert "inspect" in steps
    assert "run_tests" in steps
    assert "done" in steps

    assert not clone_dir.exists(), "Cloned repository should be cleaned up"


def test_execute_run_marks_run_gave_up(
    db,
    source_repo: Path,
    tmp_path: Path,
) -> None:
    task, run = _create_task_and_run(db)

    fake_graph = FakeGraph(
        updates=[
            {
                "run_tests": {
                    "test_output": "1 failed",
                    "tests_passed": False,
                    "attempt_count": 3,
                },
            },
        ]
    )

    clone_dir = tmp_path / "work"

    with (
        patch(
            "app.services.runs.build_agent_graph",
            return_value=fake_graph,
        ),
        patch(
            "app.services.runs.clone_repository",
            return_value=clone_dir,
        ),
    ):
        clone_dir.mkdir()
        _execute_run(
            db,
            task_id=task.id,
            run_id=run.id,
            repo_url=str(source_repo),
            task_text="Fix the add function",
        )

    db.refresh(run)
    db.refresh(task)

    assert run.status == "gave_up"
    assert run.attempts == 3
    assert task.status == "failed"


def test_execute_run_marks_run_failed_on_crash(
    db,
    source_repo: Path,
    tmp_path: Path,
) -> None:
    task, run = _create_task_and_run(db)

    fake_graph = FakeGraph(updates=[])
    fake_graph.raise_error = RuntimeError("boom")

    clone_dir = tmp_path / "work"

    with (
        patch(
            "app.services.runs.build_agent_graph",
            return_value=fake_graph,
        ),
        patch(
            "app.services.runs.clone_repository",
            return_value=clone_dir,
        ),
    ):
        clone_dir.mkdir()
        with pytest.raises(RuntimeError, match="boom"):
            _execute_run(
                db,
                task_id=task.id,
                run_id=run.id,
                repo_url=str(source_repo),
                task_text="Fix the add function",
            )

    db.refresh(run)
    db.refresh(task)

    assert run.status == "failed"
    assert "boom" in (run.error_msg or "")
    assert task.status == "failed"

    logs = crud.get_run_logs(db, run.id)

    error_logs = [log for log in logs if log.level == "error"]

    assert len(error_logs) == 1
    assert "boom" in error_logs[0].message


def test_execute_run_raises_for_missing_run(db) -> None:
    with pytest.raises(ValueError, match="does not exist"):
        _execute_run(
            db,
            task_id=1,
            run_id=999,
            repo_url="https://github.com/example/repo",
            task_text="Fix the add function",
        )
