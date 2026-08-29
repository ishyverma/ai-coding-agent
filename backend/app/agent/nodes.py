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
from app.agent.command_policy import resolve_test_command

from app.config import settings


def setup_repository_node(state: AgentState) -> AgentState:
    """Prepare the repository for the agent."""

    repo_path = state.get("repo_path")

    if repo_path:
        path = Path(repo_path).resolve()

        if not path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {repo_path}")

        if not path.is_dir():
            raise NotADirectoryError(f"Repository path is not a directory: {repo_path}")

        return {
            **state,
            "repo_path": str(path),
            "attempt_count": 0,
        }

    repo_url = state["repo_url"]

    cloned_path = clone_repository(
        repo_url=repo_url,
        base_dir=settings.agent_repo_work_dir,
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

    relevant_files = list(dict.fromkeys(test_files + important_files))

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


def _truncate_repository_contents(
    contents: dict[str, str],
    limit: int = 12_000,
) -> str:
    """
    Build a compact representation of repository contents.

    Large repositories produce prompts that exceed the LLM provider's
    token limit, so the content is capped at ``limit`` characters
    (test files first, then project files).
    """

    parts: list[str] = []
    used = 0

    for path, content in contents.items():
        available = limit - used

        if available <= 0:
            break

        block = f"--- {path} ---\n{content}"

        if len(block) > available:
            block = block[:available]

        parts.append(block)
        used += len(block)

    return "\n\n".join(parts)


def analyze_task_node(
    state: AgentState,
) -> AgentState:
    """Ask the LLM to analyze the coding task."""

    repository_contents = _truncate_repository_contents(
        state.get(
            "repository_contents",
            {},
        )
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
- Never include a file with empty content; if a file needs no
  change, omit it from the plan entirely.
- Choose the test command to match the project language:
  Python -> "pytest -q", Go -> "go test ./...",
  Node/TypeScript -> "npm test", Rust -> "cargo test".
"""

    plan = generate_code_change_plan(prompt)

    changes = [
        {
            "path": change.path,
            "content": change.content,
        }
        for change in plan.changes
        if change.path.strip() and change.content.strip()
    ]

    apply_file_changes(
        repo_path=state["repo_path"],
        changes=changes,
    )

    test_command = resolve_test_command(
        plan.test_command,
        state.get("repository_files", []),
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
        output += "\n\nSTDERR:\n" + result.stderr

    return {
        **state,
        "test_output": output,
        "tests_passed": result.passed,
        "attempt_count": state.get(
            "attempt_count",
            0,
        )
        + 1,
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
