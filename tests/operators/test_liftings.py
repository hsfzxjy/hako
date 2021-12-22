import pytest

from hako import operators as ops, boxes
from hako.boxes.dict import Dict
from hako.bricks.shaping import Hierarchy
from hako.testing.generator import Generator

from ._hyper_parameters import N_TEST_TIMES


HIERS = [
    boxes.List - boxes.Dict["foo"] - boxes.Tuple,
]

PARAMETERS = [
    (hier, level, times)
    for hier in HIERS
    for level in range(len(hier) + 1)
    for times in range(N_TEST_TIMES)
]


def lift2(hier: Hierarchy, val):
    for node in reversed(hier):
        obt = node.orig_boxtype
        if obt is boxes.List:
            val = [val]
        elif obt is boxes.Tuple:
            val = (val,)
        elif obt is boxes.Dict:
            val = {node.mdata: val}
    return val


@pytest.mark.parametrize("hier, level, _times", PARAMETERS)
def test_lift(hier: Hierarchy, level: int, _times: int):
    gen = Generator()
    x = gen.build_value(hier[level:]).retval

    out = ops.lift(hier)(x)
    expected = lift2(hier[:level], x)
    assert out == expected


def empty_object(obj, depth: int):
    type_ = obj.__class__
    if depth == 0:
        return {list: [], dict: {}, tuple: ()}[type_]

    if type_ in (list, tuple):
        return type_(empty_object(x, depth - 1) for x in obj)
    elif type_ is dict:
        return {k: empty_object(v, depth - 1) for k, v in obj.items()}


PARAMETERS = [
    (hier, level, empty_level, times)
    for hier in HIERS
    for level in range(len(hier) + 1)
    for times in range(N_TEST_TIMES)
    for empty_level in range(level, len(hier))
    if hier[empty_level].orig_boxtype is not Dict
]


@pytest.mark.parametrize("hier, level, empty_level, _times", PARAMETERS)
def test_lift_empty(hier: Hierarchy, level: int, empty_level: int, _times: int):
    gen = Generator()
    x = gen.build_value(hier[level:]).retval
    x = empty_object(x, empty_level - level)

    out = ops.lift(hier)(x)
    expected = lift2(hier[:level], x)
    assert out == expected
