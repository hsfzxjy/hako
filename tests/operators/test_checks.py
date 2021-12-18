from itertools import product

import pytest

from hako import operators as ops
from hako.bricks.shaping import Hierarchy
from hako.testing.generator import Generator

from ._hyper_parameters import HIER_CANDIDATES, N_TEST_TIMES

PARAMETERS = list(product(HIER_CANDIDATES, range(N_TEST_TIMES)))


@pytest.mark.parametrize("hier, _times", PARAMETERS)
def test_isa(hier: Hierarchy, _times: int):
    gen = Generator()
    x = gen.build_value(hier).retval
    assert ops.isa(hier)(x), x


@pytest.mark.parametrize("hier, _times", PARAMETERS)
def test_isa_diff_hier(hier: Hierarchy, _times: int):
    gen = Generator()
    result = gen.build_value(hier)
    x, x2 = result.retval, result.gen_diff_hier()
    assert not ops.isa(hier)(x2), x2
