import typing as t
from itertools import product

import pytest

from hako import operators as ops
from hako.bricks.shaping import Hierarchy
from hako.testing.generator import Generator
from hako.misc.exceptions import BoxMismatched

from ._hyper_parameters import HIER_CANDIDATES, N_TEST_TIMES


def flattenl2(objs, depth: int):
    if depth == 0:
        if len(objs) == 1:
            obj = objs[0]
        else:
            obj = tuple(objs)
        yield obj
        return

    klass = type(objs[0])
    if klass in (tuple, list):
        iterator = zip(*objs)
    elif klass is dict:
        keys = objs[0].keys()
        iterator = zip(*[[obj[k] for k in keys] for obj in objs])
    for sub in iterator:
        yield from flattenl2(sub, depth - 1)


def flatten2(objs, depth: int):
    return list(flattenl2(objs, depth))


def flatten_tester(hier: Hierarchy, args):
    output = ops.flatten(hier, lazy=False)(*args)
    expected = flatten2(args, len(hier))
    return output, expected


def map_tester(hier: Hierarchy, args):
    def _mapper(*args):
        return args if len(args) > 1 else args[0]

    output = ops.map(hier, lazy=False)(_mapper, *args)
    expected = flatten2(args, len(hier))
    return output, expected


def visit_tester(hier: Hierarchy, args):
    output = []

    def _visit_fn(*args):
        output.append(args if len(args) > 1 else args[0])

    ops.visit(hier)(_visit_fn, *args)
    expected = flatten2(args, len(hier))
    return output, expected


PARAMETERS = list(
    product(
        HIER_CANDIDATES,
        [map_tester, visit_tester, flatten_tester],
        range(N_TEST_TIMES),
    )
)

TTester = t.Callable[[Hierarchy, t.Sequence[t.Any]], t.Tuple[t.Any, t.Any]]


@pytest.mark.parametrize("hier, tester, _times", PARAMETERS)
def test_destruction(hier: Hierarchy, tester: TTester, _times: int):
    gen = Generator()
    x = gen.build_value(hier).retval
    expected, out = tester(hier, [x])
    assert out == expected


@pytest.mark.parametrize("hier, tester, _times", PARAMETERS)
def test_destruction_diff_hier(hier: Hierarchy, tester: TTester, _times: int):
    gen = Generator()
    result = gen.build_value(hier)
    x = result.gen_diff_hier()

    with pytest.raises(BoxMismatched) as ctx:
        tester(hier, [x])

    assert ctx.value.args[0].startswith("ARG has unexpected shape")


@pytest.mark.parametrize("hier, tester, _times", PARAMETERS)
def test_destruction_multi(hier: Hierarchy, tester: TTester, _times: int):
    gen = Generator()
    result = gen.build_value(hier)
    x, x2 = result.retval, result.gen_same()
    expected, out = tester(hier, [x, x2])
    assert out == expected


@pytest.mark.parametrize("hier, tester, _times", PARAMETERS)
def test_destruction_multi_diff_len(hier: Hierarchy, tester: TTester, _times: int):
    gen = Generator()
    result = gen.build_value(hier)
    x, x2 = result.retval, result.gen_diff_len()

    with pytest.raises(BoxMismatched):
        tester(hier, [x, x2])


@pytest.mark.parametrize("hier, tester, _times", PARAMETERS)
def test_destruction_multi_diff_hier(hier: Hierarchy, tester: TTester, _times: int):
    gen = Generator()
    result = gen.build_value(hier)
    x, x2 = result.retval, result.gen_diff_hier()

    with pytest.raises(BoxMismatched) as ctx:
        tester(hier, [x, x2])

    assert ctx.value.args[0].startswith("1-th ARG has unexpected shape")
