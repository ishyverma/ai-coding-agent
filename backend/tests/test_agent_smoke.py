import shutil
from pathlib import Path
from unittest.mock import patch
import pytest

from app.agent.graph import build_agent_graph
from app.agent.state import AgentState
from app.agent.schemas import CodeChangePlan, FileChange


FIXTURE_REPO = Path(__file__).parent / "fixtures" / "broken_repo"


def test_smoke_repository_exists() -> None:
    assert FIXTURE_REPO.exists()
    assert (FIXTURE_REPO / "calculator.py").exists()
    assert (FIXTURE_REPO / "tests" / "test_calculator.py").exists()


def test_agent_can_fix_broken_repository(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "broken_repo"

    shutil.copytree(
        FIXTURE_REPO,
        repo,
    )

    initial_state: AgentState = {
        "repo_path": str(repo),
        "repo_url": "",
        "task_text": ("Fix the add function so that it " "correctly adds two numbers."),
        "max_attempts": 3,
        "attempt_count": 0,
    }

    plan = CodeChangePlan(
        changes=[
            FileChange(
                path="calculator.py",
                content="""def add(a, b):
    return a + b
""",
            )
        ],
        test_command="pytest -q",
    )

    with patch(
        "app.agent.nodes.ask_llm",
        return_value="calculator.py uses multiplication where addition is required.",
    ), patch(
        "app.agent.nodes.generate_code_change_plan",
        return_value=plan,
    ):
        graph = build_agent_graph()

        state = graph.invoke(initial_state)

    assert state["tests_passed"] is True
    assert state["attempt_count"] == 1

    assert (
        (repo / "calculator.py").read_text()
        == """def add(a, b):
    return a + b
"""
    )


def test_agent_recovers_from_failed_change(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "broken_repo"

    shutil.copytree(
        FIXTURE_REPO,
        repo,
    )

    initial_state: AgentState = {
        "repo_path": str(repo),
        "repo_url": "",
        "task_text": ("Fix the add function so that it " "correctly adds two numbers."),
        "max_attempts": 3,
        "attempt_count": 0,
    }

    bad_plan = CodeChangePlan(
        changes=[
            FileChange(
                path="calculator.py",
                content="""def add(a, b):
    return a * b
""",
            )
        ],
        test_command="pytest -q",
    )

    good_plan = CodeChangePlan(
        changes=[
            FileChange(
                path="calculator.py",
                content="""def add(a, b):
    return a + b
""",
            )
        ],
        test_command="pytest -q",
    )

    with patch(
        "app.agent.nodes.ask_llm",
        return_value="calculator.py still needs the add function corrected.",
    ), patch(
        "app.agent.nodes.generate_code_change_plan",
        side_effect=[
            bad_plan,
            good_plan,
        ],
    ):
        graph = build_agent_graph()

        state = graph.invoke(initial_state)

    assert state["tests_passed"] is True
    assert state["attempt_count"] == 2

    assert (
        (repo / "calculator.py").read_text()
        == """def add(a, b):
    return a + b
"""
    )


@pytest.mark.integration
def test_real_llm_can_fix_broken_repository(
    tmp_path: Path,
) -> None:
    """Run the complete coding agent using the real LLM."""

    repo = tmp_path / "broken_repo"

    shutil.copytree(
        FIXTURE_REPO,
        repo,
    )

    initial_state: AgentState = {
        "repo_path": str(repo),
        "repo_url": "",
        "task_text": (
            "Fix the add function in calculator.py. "
            "The function is supposed to add two numbers "
            "but currently produces the wrong result. "
            "Make the smallest necessary code change "
            "and ensure the pytest tests pass."
        ),
        "max_attempts": 3,
        "attempt_count": 0,
    }

    graph = build_agent_graph()

    state = graph.invoke(initial_state)

    print("\n========== AGENT DEBUG ==========")
    print("Tests passed:", state.get("tests_passed"))
    print("Attempts:", state.get("attempt_count"))
    print("Test command:", state.get("test_command"))
    print("Test output:")
    print(state.get("test_output"))
    print("\nAnalysis:")
    print(state.get("analysis"))
    print("\nProposed changes:")
    print(state.get("proposed_changes"))
    print("\nError:")
    print(state.get("error"))

    print("\nFinal calculator.py:")
    print((repo / "calculator.py").read_text())
    print("=================================\n")
    assert state["attempt_count"] <= 3

    calculator = (repo / "calculator.py").read_text()

    assert "return a + b" in calculator
