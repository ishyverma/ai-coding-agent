from dataclasses import dataclass


@dataclass(frozen=True)
class RetryDecision:
    """Decision about whether the agent should retry."""

    should_retry: bool
    next_attempt: int
    reason: str


def decide_retry(
    *,
    tests_passed: bool,
    current_attempt: int,
    max_attempts: int,
) -> RetryDecision:
    """
    Decide whether the agent should retry after a test run.
    """

    if tests_passed:
        return RetryDecision(
            should_retry=False,
            next_attempt=current_attempt,
            reason="Tests passed.",
        )

    if current_attempt >= max_attempts:
        return RetryDecision(
            should_retry=False,
            next_attempt=current_attempt,
            reason="Maximum attempts reached.",
        )

    return RetryDecision(
        should_retry=True,
        next_attempt=current_attempt + 1,
        reason="Tests failed; another attempt is allowed.",
    )