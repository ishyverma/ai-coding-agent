from pathlib import Path
import sys

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from calculator import add


def test_add():
    assert add(2, 3) == 5
