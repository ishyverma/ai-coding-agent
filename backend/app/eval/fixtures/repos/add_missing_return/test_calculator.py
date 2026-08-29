from calculator import square


def test_square():
    assert square(4) == 16


def test_square_negative():
    assert square(-3) == 9