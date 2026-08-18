from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import crud
from app.database import Base
from app.schemas import TaskCreate


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


def setup_function() -> None:
    """Create fresh tables before every test."""
    Base.metadata.create_all(bind=test_engine)


def teardown_function() -> None:
    """Remove tables after every test."""
    Base.metadata.drop_all(bind=test_engine)


def get_test_db():
    return TestSessionLocal()


def test_create_and_get_task() -> None:
    db = get_test_db()

    task_data = TaskCreate(
        repo_url="https://github.com/example/repo",
        task_text="Fix the login function",
    )

    task = crud.create_task(db, task_data)

    assert task.id is not None
    assert task.status == "pending"

    fetched = crud.get_task(db, task.id)

    assert fetched is not None
    assert fetched.id == task.id
    assert fetched.task_text == "Fix the login function"

    db.close()


def test_list_tasks() -> None:
    db = get_test_db()

    crud.create_task(
        db,
        TaskCreate(
            repo_url="https://github.com/example/one",
            task_text="Fix issue one",
        ),
    )

    crud.create_task(
        db,
        TaskCreate(
            repo_url="https://github.com/example/two",
            task_text="Fix issue two",
        ),
    )

    tasks = crud.list_tasks(db)

    assert len(tasks) == 2

    db.close()


def test_create_run_and_logs() -> None:
    db = get_test_db()

    task = crud.create_task(
        db,
        TaskCreate(
            repo_url="https://github.com/example/repo",
            task_text="Fix tests",
        ),
    )

    run = crud.create_run(db, task.id)

    assert run.id is not None
    assert run.status == "running"
    assert run.attempts == 0

    log = crud.create_run_log(
        db,
        run.id,
        step="setup",
        message="Repository cloned",
    )

    assert log.run_id == run.id
    assert log.step == "setup"

    logs = crud.get_run_logs(db, run.id)

    assert len(logs) == 1
    assert logs[0].message == "Repository cloned"

    db.close()


def test_update_run() -> None:
    db = get_test_db()

    task = crud.create_task(
        db,
        TaskCreate(
            repo_url="https://github.com/example/repo",
            task_text="Fix tests",
        ),
    )

    run = crud.create_run(db, task.id)

    updated = crud.update_run(
        db,
        run,
        status="passed",
        attempts=2,
        tokens_used=1500,
        duration_s=12.5,
    )

    assert updated.status == "passed"
    assert updated.attempts == 2
    assert updated.tokens_used == 1500
    assert updated.duration_s == 12.5

    db.close()


def test_update_task_status() -> None:
    db = get_test_db()

    task = crud.create_task(
        db,
        TaskCreate(
            repo_url="https://github.com/example/repo",
            task_text="Fix tests",
        ),
    )

    updated = crud.update_task_status(
        db,
        task,
        "running",
    )

    assert updated.status == "running"

    db.close()