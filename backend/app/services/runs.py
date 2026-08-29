import ast
import logging
import shutil
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app import crud
from app.agent.executor import run_command
from app.agent.graph import build_agent_graph
from app.agent.llm import TokenUsage, track_tokens
from app.agent.repository import clone_repository
from app.config import settings


logger = logging.getLogger(__name__)


def _log(
    db: Session,
    run_id: int,
    step: str,
    message: str,
    level: str = "info",
    diff: str | None = None,
) -> None:
    """Write one log entry for a run."""

    crud.create_run_log(
        db,
        run_id=run_id,
        step=step,
        message=message,
        level=level,
        diff=diff,
    )


def execute_run(
    task_id: int,
    run_id: int,
    repo_url: str,
    task_text: str,
) -> None:
    """
    Execute a coding-agent run and persist its final status.

    Runs in the background after the API route returns:
    1. Clone the repository into the agent work directory.
    2. Run the LangGraph agent, logging each node as it completes.
    3. Persist the final run and task status.
    4. Clean up the cloned repository.
    """

    from app.database import SessionLocal

    db = SessionLocal()

    try:
        _execute_run(
            db,
            task_id=task_id,
            run_id=run_id,
            repo_url=repo_url,
            task_text=task_text,
        )
    except Exception:
        logger.exception("Background run failed: run_id=%s task_id=%s", run_id, task_id)
    finally:
        db.close()


def _execute_run(
    db: Session,
    task_id: int,
    run_id: int,
    repo_url: str,
    task_text: str,
) -> None:
    """Core run pipeline. Caller owns the session."""

    run = crud.get_run(db, run_id)

    if run is None:
        raise ValueError(f"Run {run_id} does not exist")

    started_at = datetime.utcnow()

    _log(
        db,
        run_id,
        "setup",
        f"Cloning repository: {repo_url}",
    )

    repo_path: Path | None = None

    try:
        repo_path = clone_repository(
            repo_url=repo_url,
            base_dir=settings.agent_repo_work_dir,
        )

        _log(
            db,
            run_id,
            "setup",
            f"Repository cloned to {repo_path}. Starting agent.",
        )

        graph = build_agent_graph()

        state = {
            "repo_path": str(repo_path),
            "task_text": task_text,
            "max_attempts": settings.agent_max_attempts,
            "attempt_count": 0,
        }

        usage = TokenUsage()

        with track_tokens(usage):
            final_state = {}

            for chunk in graph.stream(
                state,
                stream_mode="updates",
            ):
                for step_name, step_update in chunk.items():
                    if step_name == "__end__":
                        continue

                    final_state.update(step_update)
                    _log_node_step(db, run_id, step_name, step_update)

        duration = round(
            (datetime.utcnow() - started_at).total_seconds(),
            2,
        )

        final_status = _final_status(final_state)
        tests_passed = final_state.get("tests_passed", False)

        crud.update_run(
            db,
            run,
            status=final_status,
            attempts=final_state.get("attempt_count", 0),
            tokens_used=usage.total,
            duration_s=duration,
            completed_at=datetime.utcnow(),
        )

        task_final_status = "done" if tests_passed else "failed"

        task = crud.get_task(db, task_id)

        if task is not None:
            crud.update_task_status(db, task, task_final_status)

        _log(
            db,
            run_id,
            "done",
            (
                f"Agent finished: {final_status} after "
                f"{final_state.get('attempt_count', 0)} attempt(s), "
                f"{usage.total} tokens, {duration}s"
            ),
            level="info" if tests_passed else "error",
        )

    except Exception as exc:
        duration = round(
            (datetime.utcnow() - started_at).total_seconds(),
            2,
        )

        crud.update_run(
            db,
            run,
            status="failed",
            attempts=0,
            tokens_used=0,
            duration_s=duration,
            error_msg=str(exc),
            completed_at=datetime.utcnow(),
        )

        task = crud.get_task(db, task_id)

        if task is not None:
            crud.update_task_status(db, task, "failed")

        _log(
            db,
            run_id,
            "error",
            f"Agent crashed: {exc}",
            level="error",
        )
        raise

    finally:
        if repo_path is not None:
            shutil.rmtree(repo_path, ignore_errors=True)
            _log(db, run_id, "setup", "Cleaned up cloned repository.")


def _final_status(final_state: dict) -> str:
    """
    Map the graph's terminal state onto a run status.

    Status lifecycle: running -> passed | failed | gave_up
    """

    if final_state.get("tests_passed"):
        return "passed"

    attempts = final_state.get("attempt_count", 0)

    if attempts >= settings.agent_max_attempts:
        return "gave_up"

    return "failed"


def _compute_diff(repo_path: str) -> str | None:
    """Return the unified diff of all changes in the repository, if any."""

    try:
        result = run_command(
            repo_path=repo_path,
            command="git diff --no-color",
            timeout=15,
        )
    except Exception:
        return None

    if result.return_code != 0:
        return None

    output = result.stdout.strip()

    return output or None


def _format_proposed_changes(proposed: str, git_diff: str | None) -> str | None:
    """Format proposed changes as markdown code blocks."""

    if not proposed:
        return git_diff

    try:
        changes = ast.literal_eval(proposed)
    except (ValueError, SyntaxError):
        return git_diff or proposed

    if not isinstance(changes, list) or not changes:
        return git_diff

    parts: list[str] = []

    for change in changes:
        if not isinstance(change, dict):
            continue
        path = change.get("path", "")
        content = change.get("content", "")
        if not path or not content:
            continue
        ext = Path(path).suffix.lstrip(".") or "text"
        parts.append(f"### `{path}`\n\n```{ext}\n{content}\n```\n")

    if git_diff:
        parts.append(f"### Diff\n\n```diff\n{git_diff}\n```\n")

    return "\n".join(parts)


def _log_node_step(
    db: Session,
    run_id: int,
    step_name: str,
    step_update: dict,
) -> None:
    """Write a concise log entry for one completed graph node."""

    if step_name == "setup":
        message = f"Repository ready: {step_update.get('repo_path', '')}"

    elif step_name == "inspect":
        message = (
            f"Inspected {len(step_update.get('repository_files', []))} files, "
            f"{len(step_update.get('test_files', []))} test files."
        )

    elif step_name == "analyze":
        analysis = step_update.get("analysis", "")
        message = f"Analysis complete: {analysis}"

    elif step_name == "modify":
        proposed = step_update.get("proposed_changes", "")
        message = (
            f"Applied changes. Test command: {step_update.get('test_command', '')}"
        )

    elif step_name == "run_tests":
        output = step_update.get("test_output", "")
        passed = step_update.get("tests_passed", False)
        attempt = step_update.get("attempt_count", 0)
        message = (
            f"Tests {'passed' if passed else 'failed'} "
            f"(attempt {attempt}): {output}"
        )

    elif step_name == "recovery":
        message = step_update.get("error", "Preparing another attempt.")

    else:
        message = str(step_update)

    level = (
        "error"
        if step_name == "run_tests"
        and not step_update.get(
            "tests_passed",
            False,
        )
        else "info"
    )

    diff = None

    if step_name == "modify":
        git_diff = _compute_diff(step_update.get("repo_path", ""))
        proposed = step_update.get("proposed_changes", "")
        markdown_diff = _format_proposed_changes(proposed, git_diff)
        diff = markdown_diff

    _log(
        db,
        run_id,
        step_name,
        message,
        level=level,
        diff=diff,
    )
