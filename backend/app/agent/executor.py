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

    # Build a PATH that includes the active Python interpreter's bin dir plus
    # well-known locations for npm/node, go, cargo, and other language runtimes
    # so the agent can run test commands regardless of how the server was started.
    python_bin_dir = str(Path(sys.executable).resolve().parent)
    extra_paths = [
        python_bin_dir,
        # Node / npm / npx
        "/usr/local/bin",
        "/usr/bin",
        "/bin",
        # Go
        "/usr/local/go/bin",
        "/usr/local/sbin",
        # Rust / cargo (user-level install)
        str(Path.home() / ".cargo" / "bin"),
        # Homebrew (Apple Silicon)
        "/opt/homebrew/bin",
        # Homebrew (Intel)
        "/usr/local/opt/node/bin",
    ]
    existing_path = env.get("PATH", "")
    combined = os.pathsep.join(p for p in extra_paths if p not in existing_path.split(os.pathsep))
    env["PATH"] = f"{combined}{os.pathsep}{existing_path}" if existing_path else combined
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
