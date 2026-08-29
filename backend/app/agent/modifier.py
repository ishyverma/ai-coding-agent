from pathlib import Path


class UnsafeFilePathError(ValueError):
    """Raised when a requested file path escapes the repository."""


def validate_file_path(
    repo_path: str,
    file_path: str,
) -> Path:
    """
    Validate that a file path stays inside the repository.

    Returns:
        Absolute path to the requested file.
    """

    repo_root = Path(repo_path).resolve()
    target = (repo_root / file_path).resolve()

    try:
        target.relative_to(repo_root)
    except ValueError as exc:
        raise UnsafeFilePathError(f"File path escapes repository: {file_path}") from exc

    return target


def apply_file_change(
    repo_path: str,
    file_path: str,
    content: str,
) -> Path:
    """
    Write new content to one file inside the repository.
    """

    target = validate_file_path(
        repo_path,
        file_path,
    )

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    target.write_text(
        content,
        encoding="utf-8",
    )

    return target


def apply_file_changes(
    repo_path: str,
    changes: list[dict[str, str]],
) -> list[Path]:
    """
    Apply multiple file changes inside a repository.
    """

    modified_files: list[Path] = []

    for change in changes:
        path = apply_file_change(
            repo_path=repo_path,
            file_path=change["path"],
            content=change["content"],
        )

        modified_files.append(path)

    return modified_files
