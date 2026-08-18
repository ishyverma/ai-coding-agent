import json
from pathlib import Path

from app.agent.executor import run_command
from app.agent.inspector import (
    detect_file_extensions,
    find_important_files,
    find_test_files,
    list_repository_files,
)
from app.agent.llm import ask_llm
from app.agent.modifier import apply_file_changes
from app.agent.recovery import decide_retry
from app.agent.repository import clone_repository
from app.agent.state import AgentState


def setup_repository_node(state: AgentState) -> AgentState:
    """Clone the repository into an isolated workspace."""

    repo_url = state["repo_url"]

    repo_path = clone_repository(
        repo_url=repo_url,
        base_dir="/tmp/agent-repos",
    )

    return {
        **state,
        "repo_path": str(repo_path),
        "attempt_count": 0,
    }


def inspect_repository_node(
    state: AgentState,
) -> AgentState:
    """Inspect the cloned repository."""

    repo_path = state["repo_path"]

    files = list_repository_files(repo_path)
    test_files = find_test_files(repo_path)
    important_files = find_important_files(repo_path)
    extensions = detect_file_extensions(repo_path)

    return {
        **state,
        "repository_files": files,
        "test_files": test_files,
        "important_files": important_files,
        "file_extensions": extensions,
    }


def analyze_task_node(
    state: AgentState,
) -> AgentState:
    """Ask the LLM to analyze the coding task."""

    files = "\n".join(
        state.get("repository_files", [])
    )

    important_files = "\n".join(
        state.get("important_files", [])
    )

    test_files = "\n".join(
        state.get("test_files", [])
    )

    prompt = f"""
You are an expert software engineer.

Analyze the following coding task.

TASK:
{state["task_text"]}

REPOSITORY FILES:
{files}

IMPORTANT PROJECT FILES:
{important_files}

TEST FILES:
{test_files}

Return:
1. What is likely wrong.
2. Which files are likely relevant.
3. What change should be made.
4. What test command should be run.

Do not modify files yourself.
Provide a concise technical analysis.
"""

    analysis = ask_llm(prompt)

    return {
        **state,
        "analysis": analysis,
    }


def modify_code_node(
    state: AgentState,
) -> AgentState:
    """Ask the LLM for code changes and apply them."""

    prompt = f"""
You are an expert software engineer.

TASK:
{state["task_text"]}

REPOSITORY FILES:
{chr(10).join(state["repository_files"])}

ANALYSIS:
{state["analysis"]}

Return ONLY valid JSON in this exact format:

{{
    "changes": [
        {{
            "path": "relative/path/to/file.py",
            "content": "complete new file content"
        }}
    ],
    "test_command": "pytest -q"
}}

Rules:
- Paths must be relative to the repository root.
- Do not use absolute paths.
- Do not use ../.
- Return complete file contents.
- Do not include markdown fences.
"""

    response = ask_llm(prompt)

    try:
        result = json.loads(response)
    except json.JSONDecodeError as exc:
        return {
            **state,
            "error": f"LLM returned invalid JSON: {exc}",
        }

    changes = result.get("changes", [])
    test_command = result.get(
        "test_command",
        "pytest -q",
    )

    modified_files = apply_file_changes(
        repo_path=state["repo_path"],
        changes=changes,
    )

    return {
        **state,
        "test_command": test_command,
        "proposed_changes": json.dumps(
            changes
        ),
    }


def run_tests_node(
    state: AgentState,
) -> AgentState:
    """Run the repository's test command."""

    command = state.get(
        "test_command",
        "pytest -q",
    )

    result = run_command(
        repo_path=state["repo_path"],
        command=command,
        timeout=60,
    )

    output = result.stdout

    if result.stderr:
        output += (
            "\n\nSTDERR:\n"
            + result.stderr
        )

    return {
        **state,
        "test_output": output,
        "tests_passed": result.passed,
    }


def recovery_node(
    state: AgentState,
) -> AgentState:
    """Decide whether another attempt is allowed."""

    decision = decide_retry(
        tests_passed=state.get(
            "tests_passed",
            False,
        ),
        current_attempt=state.get(
            "attempt_count",
            0,
        ),
        max_attempts=state["max_attempts"],
    )

    return {
        **state,
        "attempt_count": decision.next_attempt,
        "error": decision.reason,
    }


def route_after_tests(
    state: AgentState,
) -> str:
    """Determine the next graph node after testing."""

    if state.get("tests_passed", False):
        return "done"

    decision = decide_retry(
        tests_passed=False,
        current_attempt=state.get(
            "attempt_count",
            0,
        ),
        max_attempts=state["max_attempts"],
    )

    if decision.should_retry:
        return "analyze"

    return "failed"