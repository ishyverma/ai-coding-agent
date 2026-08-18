import subprocess
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

        return (
            self.return_code == 0
            and not self.timed_out
        )


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
        raise FileNotFoundError(
            f"Repository path does not exist: {repo_path}"
        )

    if not repo.is_dir():
        raise NotADirectoryError(
            f"Repository path is not a directory: {repo_path}"
        )

    try:
        result = subprocess.run(
            command,
            cwd=repo,
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