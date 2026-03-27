import pytest

from rimpack.tools import normalize_rimworld_version


@pytest.mark.parametrize(
    ["raw", "expected"],
    [
        ("1", 1.0),
        ("v1.4", 1.4),
        ("1.6", 1.6),
        ("1.6.1", 1.6),
        ("1.6.4633 rev1260", 1.6),
    ],
)
def test_normalize_rimworld_version(raw: str, expected: float):
    result = normalize_rimworld_version(raw)
    assert result == expected
