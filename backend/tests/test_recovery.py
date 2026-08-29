from app.agent.recovery import decide_retry


def test_retry_when_tests_fail_and_attempts_remain() -> None:
    decision = decide_retry(
        tests_passed=False,
        current_attempt=1,
        max_attempts=3,
    )

    assert decision.should_retry is True
    assert decision.next_attempt == 2
    assert "another attempt" in decision.reason


def test_retry_on_second_attempt() -> None:
    decision = decide_retry(
        tests_passed=False,
        current_attempt=2,
        max_attempts=3,
    )

    assert decision.should_retry is True
    assert decision.next_attempt == 3


def test_stop_after_max_attempts() -> None:
    decision = decide_retry(
        tests_passed=False,
        current_attempt=3,
        max_attempts=3,
    )

    assert decision.should_retry is False
    assert decision.next_attempt == 3
    assert "Maximum attempts" in decision.reason


def test_success_stops_retrying() -> None:
    decision = decide_retry(
        tests_passed=True,
        current_attempt=1,
        max_attempts=3,
    )

    assert decision.should_retry is False
    assert decision.next_attempt == 1
    assert "Tests passed" in decision.reason


def test_success_on_final_attempt_still_stops() -> None:
    decision = decide_retry(
        tests_passed=True,
        current_attempt=3,
        max_attempts=3,
    )

    assert decision.should_retry is False
    assert decision.next_attempt == 3
