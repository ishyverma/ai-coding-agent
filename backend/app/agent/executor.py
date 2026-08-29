import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CommandResult:
    """Result of executing a repository command."""

    command: str
    return_code: int
    stdout: str
    stderr: str
    timed_out: bool

    @property
    def passed(self) -> bool:
        """Whether the command completed successfully."""

        return self.return_code == 0 and not self.timed_out


def _portable_command(command: str) -> str:
    """Rewrite common Python commands to the active interpreter."""

    python = shlex.quote(sys.executable)

    if command == "python":
        return python

    if command.startswith("python "):
        return f"{python} {command.removeprefix('python ')}"

    if command == "pytest":
        return f"{python} -m pytest"

    if command.startswith("pytest "):
        return f"{python} -m pytest {command.removeprefix('pytest ')}"

    return command


def _is_python_command(command: str) -> bool:
    """Return whether a command executes Python code or tests."""

    return command == "python" or command.startswith(("python ", "pytest"))


def _clear_python_caches(repo: Path) -> None:
    """Remove stale bytecode so repeated agent edits test fresh source."""

    for cache_dir in repo.rglob("__pycache__"):
        shutil.rmtree(cache_dir, ignore_errors=True)


def run_command(
    repo_path: str,
    command: str,
    timeout: int = 60,
) -> CommandResult:
    """
    Execute a command inside the repository.

    The command's stdout/stderr are captured and returned.
    """

    repo = Path(repo_path).resolve()

    if not repo.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repo_path}")

    if not repo.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {repo_path}")

    if _is_python_command(command):
        _clear_python_caches(repo)

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    python_bin_dir = str(Path(sys.executable).resolve().parent)
    env["PATH"] = f"{python_bin_dir}{os.pathsep}{env.get('PATH', '')}"
    resolved_command = _portable_command(command)

    try:
        result = subprocess.run(
            resolved_command,
            check=False,
            cwd=repo,
            env=env,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return CommandResult(
            command=command,
            return_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=False,
        )

    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""

        if isinstance(stdout, bytes):
            stdout = stdout.decode(
                "utf-8",
                errors="replace",
            )

        if isinstance(stderr, bytes):
            stderr = stderr.decode(
                "utf-8",
                errors="replace",
            )

        return CommandResult(
            command=command,
            return_code=-1,
            stdout=stdout,
            stderr=stderr,
            timed_out=True,
        )
