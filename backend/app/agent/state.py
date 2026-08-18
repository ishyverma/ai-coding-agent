from typing import TypedDict


class AgentState(TypedDict, total=False):
    """
    Shared state passed between LangGraph agent nodes.
    """

    # ── Task information ──────────────────────────────────────────────────────
    task_id: int
    repo_url: str
    task_text: str

    # ── Repository information ────────────────────────────────────────────────
    repo_path: str
    repository_files: list[str]
    test_files: list[str]
    important_files: list[str]
    file_extensions: dict[str, int]

    # ── Agent reasoning ────────────────────────────────────────────────────────
    analysis: str
    proposed_changes: str

    # ── Execution information ─────────────────────────────────────────────────
    test_command: str
    test_output: str
    tests_passed: bool

    # ── Retry information ──────────────────────────────────────────────────────
    attempt_count: int
    max_attempts: int

    # ── Error information ─────────────────────────────────────────────────────
    error: str