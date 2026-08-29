from dataclasses import dataclass

from app.eval.runner import TaskResult


@dataclass
class EvalScore:
    """Aggregate score for an eval run."""

    pass_rate: float  # 0.0 to 1.0
    avg_attempts: float  # lower = more efficient
    avg_tokens: float  # lower = cheaper to run
    avg_duration_s: float  # lower = faster
    total: int
    passed: int
    failed: int


def compute_score(results: list[TaskResult]) -> EvalScore:
    """
    Compute aggregate metrics across all eval task results.

    These 4 metrics mirror what SWE-bench (the industry benchmark
    for coding agents) uses:
    - pass_rate: does the agent get it right?
    - avg_attempts: is it efficient? (3 attempts = it struggled)
    - avg_tokens: is it economical? (high tokens = expensive)
    - avg_duration_s: is it fast? (user experience)

    When you change the model or prompt, run the eval again and
    compare these numbers. That's how you know if your change was
    an improvement.
    """

    if not results:
        return EvalScore(
            pass_rate=0.0,
            avg_attempts=0.0,
            avg_tokens=0.0,
            avg_duration_s=0.0,
            total=0,
            passed=0,
            failed=0,
        )

    total = len(results)
    passed = sum(1 for r in results if r.passed)

    return EvalScore(
        pass_rate=round(passed / total, 3),
        avg_attempts=round(sum(r.attempts for r in results) / total, 2),
        avg_tokens=round(sum(r.tokens_used for r in results) / total, 0),
        avg_duration_s=round(sum(r.duration_s for r in results) / total, 2),
        total=total,
        passed=passed,
        failed=total - passed,
    )
