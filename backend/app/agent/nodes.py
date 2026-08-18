from pathlib import Path

from app.agent.executor import run_command
from app.agent.inspector import (
    detect_file_extensions,
    find_important_files,
    find_test_files,
    list_repository_files,
    read_repository_files,
)
from app.agent.llm import (
    ask_llm,
    generate_code_change_plan,
)
from app.agent.modifier import apply_file_changes
from app.agent.recovery import decide_retry
from app.agent.repository import clone_repository
from app.agent.state import AgentState
from app.agent.command_policy import validate_test_command

def setup_repository_node(state: AgentState) -> AgentState:
    """Prepare the repository for the agent."""

    repo_path = state.get("repo_path")

    if repo_path:
        path = Path(repo_path).resolve()

        if not path.exists():
            raise FileNotFoundError(
                f"Repository path does not exist: {repo_path}"
            )

        if not path.is_dir():
            raise NotADirectoryError(
                f"Repository path is not a directory: {repo_path}"
            )

        return {
            **state,
            "repo_path": str(path),
            "attempt_count": 0,
        }

    repo_url = state["repo_url"]

    cloned_path = clone_repository(
        repo_url=repo_url,
        base_dir="/tmp/agent-repos",
    )

    return {
        **state,
        "repo_path": str(cloned_path),
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

    relevant_files = list(
        dict.fromkeys(
            important_files + test_files
        )
    )

    contents = read_repository_files(
        repo_path,
        relevant_files,
    )

    return {
        **state,
        "repository_files": files,
        "test_files": test_files,
        "important_files": important_files,
        "file_extensions": extensions,
        "repository_contents": contents,
    }
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

    repository_contents = "\n\n".join(
        f"--- {path} ---\n{content}"
        for path, content in state.get(
            "repository_contents",
            {},
        ).items()
    )

    previous_test_output = state.get(
    "test_output",
    "",
)

    prompt = f"""
You are an expert software engineer.

Analyze the following coding task and repository.

TASK:
{state["task_text"]}

REPOSITORY FILES:
{chr(10).join(state.get("repository_files", []))}

IMPORTANT FILES:
{chr(10).join(state.get("important_files", []))}

TEST FILES:
{chr(10).join(state.get("test_files", []))}

SOURCE CODE:
{repository_contents}

PREVIOUS TEST OUTPUT:
{previous_test_output}

Provide a concise technical analysis of:
1. What is wrong.
2. Which files are relevant.
3. What should be changed.
4. What test command should be used.

If previous test output is present, use it to understand
why the previous attempt failed.
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

Return a structured code change plan.

Rules:
- Paths must be relative to the repository root.
- Never use absolute paths.
- Never use ../.
- Return complete file contents.
- Only modify files necessary to solve the task.
- Use pytest for Python projects when appropriate.
"""

    plan = generate_code_change_plan(prompt)

    changes = [
        {
            "path": change.path,
            "content": change.content,
        }
        for change in plan.changes
    ]

    apply_file_changes(
        repo_path=state["repo_path"],
        changes=changes,
    )

    test_command = validate_test_command(
        plan.test_command
    )

    return {
        **state,
        "test_command": test_command,
        "proposed_changes": str(changes),
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
        "attempt_count": state.get(
            "attempt_count",
            0,
        ) + 1,
    }
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
        "error": decision.reason,
    }
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