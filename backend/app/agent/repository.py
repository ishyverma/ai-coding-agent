from pathlib import Path
from uuid import uuid4

from git import Repo


def create_work_directory(base_dir: str) -> Path:
    """
    Create a unique directory for one agent run.
    """

    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    work_dir = base_path / str(uuid4())
    work_dir.mkdir(parents=True, exist_ok=False)

    return work_dir


def clone_repository(
    repo_url: str,
    base_dir: str,
) -> Path:
    """
    Clone a Git repository into an isolated working directory.

    Returns:
        Path to the cloned repository.
    """

    work_dir = create_work_directory(base_dir)

    Repo.clone_from(
        repo_url,
        work_dir,
    )

    return work_dir
