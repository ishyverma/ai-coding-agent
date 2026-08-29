from app.agent.state import AgentState


def test_agent_state_can_store_task_information() -> None:
    state: AgentState = {
        "task_id": 1,
        "repo_url": "https://github.com/example/repo",
        "task_text": "Fix the login bug",
        "attempt_count": 0,
        "max_attempts": 3,
    }

    assert state["task_id"] == 1
    assert state["repo_url"] == "https://github.com/example/repo"
    assert state["attempt_count"] == 0
    assert state["max_attempts"] == 3


def test_agent_state_can_store_execution_results() -> None:
    state: AgentState = {
        "tests_passed": True,
        "test_output": "5 passed",
        "attempt_count": 1,
    }

    assert state["tests_passed"] is True
    assert state["test_output"] == "5 passed"
