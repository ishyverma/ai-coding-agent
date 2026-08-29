from grade_checker import is_passing


def test_failing():
    assert is_passing(50) is False


def test_passing():
    assert is_passing(75) is True


def test_boundary():
    assert is_passing(60) is True  # fails with >