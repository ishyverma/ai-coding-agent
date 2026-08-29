from app.eval.runner import TaskResult
from app.eval.scorer import compute_score


def _result(
    name: str,
    passed: bool,
    attempts: int = 1,
    tokens: int = 100,
    duration: float = 10.0,
) -> TaskResult:
    return TaskResult(
        name=name,
        passed=passed,
        attempts=attempts,
        tokens_used=tokens,
        duration_s=duration,
    )


def test_compute_score_empty_results() -> None:
    score = compute_score([])

    assert score.total == 0
    assert score.passed == 0
    assert score.failed == 0
    assert score.pass_rate == 0.0


def test_compute_score_mixed_results() -> None:
    results = [
        _result("a", passed=True, attempts=1, tokens=100, duration=10.0),
        _result("b", passed=True, attempts=2, tokens=200, duration=20.0),
        _result("c", passed=False, attempts=3, tokens=300, duration=30.0),
    ]

    score = compute_score(results)

    assert score.total == 3
    assert score.passed == 2
    assert score.failed == 1
    assert score.pass_rate == 0.667
    assert score.avg_attempts == 2.0
    assert score.avg_tokens == 200
    assert score.avg_duration_s == 20.0


def test_compute_score_all_passed() -> None:
    results = [
        _result("a", passed=True),
        _result("b", passed=True),
    ]

    score = compute_score(results)

    assert score.pass_rate == 1.0
    assert score.failed == 0
