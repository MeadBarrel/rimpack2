from rimpack.core.toposort import stable_toposort, ToposortItem, CycleError
import pytest


def test_stable_toposort():
    items = [
        ToposortItem(0, before=[1]),
        ToposortItem(1),
        ToposortItem(2, after=[4]),
        ToposortItem(3),
        ToposortItem(4, before=[2], after=[5]),
        ToposortItem(5),
        ToposortItem(6),
        ToposortItem(7, before=[4]),
        ToposortItem(8, before=[1, 2]),
        ToposortItem(9, before=[3, 6], after=[1]),
    ]
    expected = [0, 8, 1, 9, 3, 5, 7, 4, 2, 6]
    result = stable_toposort(items)
    assert result == expected


def test_stable_toposort_cycle():
    items = [
        ToposortItem(0),
        ToposortItem(1, before=[2]),
        ToposortItem(2, before=[1]),
    ]
    with pytest.raises(CycleError):
        _ = stable_toposort(items)
