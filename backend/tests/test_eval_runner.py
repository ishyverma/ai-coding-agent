import json
from pathlib import Path
from unittest.mock import patch

from app.eval.runner import EvalRunner

REAL_FIXTURES_DIR = Path(__file__).parent.parent / "app" / "eval" / "fixtures"


def test_load_tasks_loads_all_fixtures() -> None:
    runner = EvalRunner(fixtures_dir=REAL_FIXTURES_DIR)

    tasks = runner.load_tasks()

    names = {task["name"] for task in tasks}

    assert names == {
        "fix_off_by_one",
        "add_missing_return",
        "fix_wrong_variable",
        "add_missing_function",
        "fix_wrong_operator",
    }


def test_resolve_repo_url_keeps_remote_urls() -> None:
    runner = EvalRunner(fixtures_dir=REAL_FIXTURES_DIR)

    assert (
        runner._resolve_repo_url("https://github.com/user/repo")
        == "https://github.com/user/repo"
    )


def test_resolve_repo_url_resolves_local_path() -> None:
    runner = EvalRunner(fixtures_dir=REAL_FIXTURES_DIR)

    resolved = runner._resolve_repo_url("repos/fix_off_by_one")

    assert resolved.endswith("repos/fix_off_by_one")
    assert Path(resolved).is_dir()


class FakeGraph:
    """Minimal stand-in that always returns tests_passed=True."""

    def __init__(self, tests_passed: bool = True) -> None:
        self.tests_passed = tests_passed

    def invoke(self, state) -> dict:
        return {
            "tests_passed": self.tests_passed,
            "attempt_count": 1,
        }


def test_run_one_returns_passed_result(tmp_path: Path) -> None:
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()

    task_def = {
        "name": "fix_off_by_one",
        "description": "Fix the bug.",
        "repo_url": str(REAL_FIXTURES_DIR / "repos" / "fix_off_by_one"),
    }

    runner = EvalRunner(fixtures_dir=fixtures_dir)

    with patch(
        "app.eval.runner.build_agent_graph",
        return_value=FakeGraph(tests_passed=True),
    ):
        result = runner._run_one(task_def)

    assert result.name == "fix_off_by_one"
    assert result.passed is True
    assert result.attempts == 1
    assert result.duration_s >= 0


def test_run_one_returns_failed_result_on_graph_error(tmp_path: Path) -> None:
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()

    task_def = {
        "name": "broken_task",
        "description": "Fix the bug.",
        "repo_url": str(REAL_FIXTURES_DIR / "repos" / "fix_off_by_one"),
    }

    runner = EvalRunner(fixtures_dir=fixtures_dir)

    class ExplodingGraph:
        def invoke(self, state) -> dict:
            raise RuntimeError("LLM unavailable")

    with patch(
        "app.eval.runner.build_agent_graph",
        return_value=ExplodingGraph(),
    ):
        result = runner._run_one(task_def)

    assert result.passed is False
    assert result.error == "LLM unavailable"


def test_run_collects_all_task_results(tmp_path: Path) -> None:
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()

    for name in ("one", "two"):
        (fixtures_dir / f"{name}.json").write_text(
            json.dumps(
                {
                    "name": name,
                    "description": f"Fix {name}",
                    "repo_url": str(REAL_FIXTURES_DIR / "repos" / "fix_off_by_one"),
                }
            )
        )

    runner = EvalRunner(fixtures_dir=fixtures_dir)

    with patch(
        "app.eval.runner.build_agent_graph",
        return_value=FakeGraph(tests_passed=True),
    ):
        results = runner.run()

    assert len(results) == 2
    assert all(result.passed for result in results)
