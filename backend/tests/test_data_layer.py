from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import crud
from app.database import Base
from app.schemas import TaskCreate, TaskResponse


TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def setup_function() -> None:
    Base.metadata.create_all(bind=engine)


def teardown_function() -> None:
    Base.metadata.drop_all(bind=engine)


def get_db():
    return TestingSessionLocal()


def test_task_complete_data_flow() -> None:
    """Test TaskCreate → CRUD → database → retrieval."""

    db = get_db()

    # 1. Create request data.
    task_data = TaskCreate(
        repo_url="https://github.com/example/project",
        task_text="Fix authentication bug",
    )

    # 2. Save through CRUD.
    task = crud.create_task(db, task_data)

    # 3. Verify database object.
    assert task.id is not None
    assert task.repo_url == task_data.repo_url
    assert task.task_text == task_data.task_text
    assert task.status == "pending"

    # 4. Retrieve from database.
    fetched_task = crud.get_task(db, task.id)

    assert fetched_task is not None
    assert fetched_task.id == task.id

    # 5. Convert database object → API response schema.
    response = TaskResponse.model_validate(fetched_task)

    assert response.id == task.id
    assert response.repo_url == task.repo_url
    assert response.status == "pending"
    assert isinstance(response.created_at, datetime)

    db.close()


def test_task_run_log_relationship_flow() -> None:
    """Test Task → Run → RunLog relationships."""

    db = get_db()

    task = crud.create_task(
        db,
        TaskCreate(
            repo_url="https://github.com/example/project",
            task_text="Fix failing tests",
        ),
    )

    run = crud.create_run(db, task.id)

    crud.create_run_log(
        db,
        run.id,
        step="setup",
        message="Repository cloned",
    )

    crud.create_run_log(
        db,
        run.id,
        step="test",
        message="Running test suite",
    )

    logs = crud.get_run_logs(db, run.id)

    assert len(logs) == 2
    assert logs[0].step == "setup"
    assert logs[1].step == "test"

    # Verify relationships from SQLAlchemy.
    fetched_run = crud.get_run(db, run.id)

    assert fetched_run is not None
    assert fetched_run.task.id == task.id
    assert len(fetched_run.logs) == 2

    db.close()


def test_run_lifecycle() -> None:
    """Test a run progressing from running to passed."""

    db = get_db()

    task = crud.create_task(
        db,
        TaskCreate(
            repo_url="https://github.com/example/project",
            task_text="Fix failing tests",
        ),
    )

    run = crud.create_run(db, task.id)

    assert run.status == "running"

    completed_at = datetime.now()

    updated_run = crud.update_run(
        db,
        run,
        status="passed",
        attempts=2,
        tokens_used=2500,
        duration_s=15.4,
        completed_at=completed_at,
    )

    assert updated_run.status == "passed"
    assert updated_run.attempts == 2
    assert updated_run.tokens_used == 2500
    assert updated_run.duration_s == 15.4
    assert updated_run.completed_at == completed_at

    db.close()