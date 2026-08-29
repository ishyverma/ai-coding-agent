from pathlib import Path


# Directories that are usually not useful for code analysis.
IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
}


# Files that can contain useful project-level information.
IMPORTANT_FILES = {
    "README.md",
    "README",
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "package-lock.json",
    "tsconfig.json",
    "go.mod",
    "go.sum",
    "Cargo.toml",
    "Makefile",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".gitignore",
}


def list_repository_files(repo_path: str) -> list[str]:
    """
    Return repository files using paths relative to the repository root.
    """

    root = Path(repo_path)

    if not root.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repo_path}")

    if not root.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {repo_path}")

    files: list[str] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        relative_path = path.relative_to(root)

        # Ignore files inside excluded directories.
        if any(part in IGNORED_DIRECTORIES for part in relative_path.parts):
            continue

        files.append(relative_path.as_posix())

    return sorted(files)


def find_test_files(repo_path: str) -> list[str]:
    """
    Find files that look like test files.
    """

    files = list_repository_files(repo_path)

    test_files = [
        path
        for path in files
        if (
            path.startswith("tests/")
            or "/tests/" in path
            or Path(path).name.startswith("test_")
            or Path(path).name.endswith("_test.py")
            or Path(path).name.endswith("_test.go")
            or Path(path).name.endswith("_test.rs")
            or Path(path).name.endswith(
                (".test.ts", ".test.tsx", ".test.js", ".test.jsx")
            )
            or Path(path).name.endswith(
                (".spec.ts", ".spec.tsx", ".spec.js", ".spec.jsx")
            )
        )
    ]

    return sorted(test_files)


def find_important_files(repo_path: str) -> list[str]:
    """
    Find common project-level configuration/documentation files.
    """

    files = list_repository_files(repo_path)

    return sorted(path for path in files if Path(path).name in IMPORTANT_FILES)


def detect_file_extensions(repo_path: str) -> dict[str, int]:
    """
    Count files by extension.
    """

    files = list_repository_files(repo_path)

    extensions: dict[str, int] = {}

    for file_path in files:
        suffix = Path(file_path).suffix.lower()

        if not suffix:
            continue

        extensions[suffix] = extensions.get(suffix, 0) + 1

    return dict(sorted(extensions.items()))


def read_repository_files(
    repo_path: str,
    files: list[str],
    max_file_size: int = 50_000,
) -> dict[str, str]:
    """
    Read the contents of selected repository files.

    Large files are skipped to avoid sending excessive
    source code to the LLM.
    """

    repo = Path(repo_path).resolve()

    contents: dict[str, str] = {}

    for relative_path in files:
        file_path = (repo / relative_path).resolve()

        # Prevent path traversal.
        try:
            file_path.relative_to(repo)
        except ValueError:
            continue

        if not file_path.is_file():
            continue

        if file_path.stat().st_size > max_file_size:
            continue

        try:
            contents[relative_path] = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

    return contents
