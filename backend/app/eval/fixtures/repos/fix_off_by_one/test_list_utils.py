from list_utils import last_element


def test_last_element():
    assert last_element([1, 2, 3]) == 3


def test_last_single():
    assert last_element([42]) == 42