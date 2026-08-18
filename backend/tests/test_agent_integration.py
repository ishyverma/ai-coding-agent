from pathlib import Path
from unittest.mock import patch

from app.agent.schemas import (
    CodeChangePlan,
    FileChange,
)
from app.agent.graph import build_agent_graph
from app.agent.state import AgentState


def create_initial_state(
    repo_url: str = "https://github.com/example/repo",
) -> AgentState:
    """Create the minimum state required to start the graph."""

    return {
        "task_id": 1,
        "repo_url": repo_url,
        "task_text": "Fix the failing test",
        "max_attempts": 3,
        "attempt_count": 0,
    }


def test_agent_graph_successful_run(tmp_path: Path) -> None:
    """The graph should complete when tests pass."""

    fake_repo = tmp_path / "repo"
    fake_repo.mkdir()

    with (
        patch(
            "app.agent.nodes.clone_repository",
            return_value=fake_repo,
        ),
        patch(
            "app.agent.nodes.generate_code_change_plan",
            return_value=CodeChangePlan(
                changes=[],
                test_command="pytest -q",
            ),
        ),
        patch(
            "app.agent.nodes.apply_file_changes",
            return_value=[
                fake_repo / "src" / "main.py"
            ],
        ),
        patch(
            "app.agent.nodes.run_command",
        ) as mock_run_command,
    ):
        mock_run_command.return_value.passed = True
        mock_run_command.return_value.stdout = "1 passed"
        mock_run_command.return_value.stderr = ""
        mock_run_command.return_value.return_code = 0
        mock_run_command.return_value.timed_out = False

        graph = build_agent_graph()

        state = graph.invoke(
            create_initial_state()
        )

    assert state["tests_passed"] is True
    assert state["test_output"] == "1 passed"
    assert state["attempt_count"] == 1


def test_agent_graph_retries_after_failure(
    tmp_path: Path,
) -> None:
    """The graph should retry when the first test run fails."""

    fake_repo = tmp_path / "repo"
    fake_repo.mkdir()

    with (
        patch(
            "app.agent.nodes.clone_repository",
            return_value=fake_repo,
        ),
       patch(
            "app.agent.nodes.generate_code_change_plan",
            return_value=CodeChangePlan(
                changes=[],
                test_command="pytest -q",
            ),
        ),
        patch(
            "app.agent.nodes.apply_file_changes",
            return_value=[],
        ),
        patch(
            "app.agent.nodes.run_command",
        ) as mock_run_command,
    ):
        first_result = type(
            "Result",
            (),
            {
                "passed": False,
                "stdout": "1 failed",
                "stderr": "AssertionError",
                "return_code": 1,
                "timed_out": False,
            },
        )()

        second_result = type(
            "Result",
            (),
            {
                "passed": True,
                "stdout": "1 passed",
                "stderr": "",
                "return_code": 0,
                "timed_out": False,
            },
        )()

        mock_run_command.side_effect = [
            first_result,
            second_result,
        ]

        graph = build_agent_graph()

        state = graph.invoke(
            create_initial_state()
        )

    assert state["tests_passed"] is True
    assert state["attempt_count"] == 2

    assert mock_run_command.call_count == 2


def test_agent_graph_stops_after_max_attempts(
    tmp_path: Path,
) -> None:
    """The graph should stop after the configured maximum attempts."""

    fake_repo = tmp_path / "repo"
    fake_repo.mkdir()

    with (
        patch(
            "app.agent.nodes.clone_repository",
            return_value=fake_repo,
        ),
        patch(
            "app.agent.nodes.generate_code_change_plan",
            return_value=CodeChangePlan(
                changes=[],
                test_command="pytest -q",
            ),
        ),
        patch(
            "app.agent.nodes.apply_file_changes",
            return_value=[],
        ),
        patch(
            "app.agent.nodes.run_command",
        ) as mock_run_command,
    ):
        failed_result = type(
            "Result",
            (),
            {
                "passed": False,
                "stdout": "1 failed",
                "stderr": "AssertionError",
                "return_code": 1,
                "timed_out": False,
            },
        )()

        mock_run_command.return_value = failed_result

        graph = build_agent_graph()

        initial_state = create_initial_state()
        initial_state["max_attempts"] = 3

        state = graph.invoke(initial_state)

    assert state["tests_passed"] is False
    assert mock_run_command.call_count == 3
    assert state["attempt_count"] == 3