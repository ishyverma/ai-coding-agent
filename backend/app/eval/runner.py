import json
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import git

from app.agent.graph import build_agent_graph
from app.agent.llm import TokenUsage, track_tokens
from app.config import settings

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@dataclass
class TaskResult:
    """Result for a single eval task."""

    name: str
    passed: bool
    attempts: int
    tokens_used: int
    duration_s: float
    error: str = ""


class EvalRunner:
    """
    Runs the agent against pre-made broken repos and collects results.

    Usage:
        runner = EvalRunner()
        results = runner.run()   # returns list[TaskResult]
    """

    def __init__(self, fixtures_dir: Path = FIXTURES_DIR) -> None:
        self.fixtures_dir = fixtures_dir

    def load_tasks(self) -> list[dict]:
        """Load all .json eval task definitions from the fixtures folder."""

        tasks = []

        for path in sorted(self.fixtures_dir.glob("*.json")):
            with path.open() as f:
                tasks.append(json.load(f))

        return tasks

    def _resolve_repo_url(self, repo_url: str) -> str:
        """
        Resolve a task's repo_url.

        GitHub URLs are cloned as-is. Relative paths are resolved
        against the fixtures directory so the eval suite can run
        against the bundled local repos without a network.
        """

        if repo_url.startswith(("http://", "https://", "git@")):
            return repo_url

        return str((self.fixtures_dir / repo_url).resolve())

    def run(self) -> list[TaskResult]:
        """Run all eval tasks and return the results."""

        tasks = self.load_tasks()
        print(f"Running eval on {len(tasks)} tasks...")

        results = []

        for i, task_def in enumerate(tasks, 1):
            print(f"  [{i}/{len(tasks)}] Running: {task_def['name']}")

            result = self._run_one(task_def)
            results.append(result)

            status = "✓ PASS" if result.passed else "✗ FAIL"
            print(
                f"          {status} ({result.attempts} attempts, "
                f"{result.duration_s}s)"
            )

        return results

    def _run_one(self, task_def: dict) -> TaskResult:
        """Clone or copy the repo, run the agent, return the result."""

        repo_path = Path(tempfile.mkdtemp())
        start = time.time()

        try:
            repo_url = self._resolve_repo_url(task_def["repo_url"])
            src = Path(repo_url)
            if src.is_dir():
                shutil.copytree(str(src), str(repo_path))
            else:
                git.Repo.clone_from(repo_url, str(repo_path))

            graph = build_agent_graph()

            initial_state = {
                "repo_path": str(repo_path),
                "task_text": task_def["description"],
                "max_attempts": settings.agent_max_attempts,
                "attempt_count": 0,
            }

            usage = TokenUsage()

            with track_tokens(usage):
                final_state = graph.invoke(initial_state)

            duration = round(time.time() - start, 2)

            return TaskResult(
                name=task_def["name"],
                passed=final_state.get("tests_passed", False),
                attempts=final_state.get("attempt_count", 0),
                tokens_used=usage.total,
                duration_s=duration,
            )

        except Exception as exc:
            return TaskResult(
                name=task_def["name"],
                passed=False,
                attempts=0,
                tokens_used=0,
                duration_s=round(time.time() - start, 2),
                error=str(exc),
            )

        finally:
            shutil.rmtree(str(repo_path), ignore_errors=True)
