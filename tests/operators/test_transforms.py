import typing as t
from itertools import permutations

import pytest
import numpy as np

from hako import boxes, operators as ops
from hako.bricks.shaping import Hierarchy, create_hierarchy_nocheck
from hako.boxes.dict import MultiItemsDict, SingleItemDict, VariadicDict
from hako.testing.generator import HierarchyWrapper

from ._hyper_parameters import N_TEST_TIMES, HIER_CANDIDATES


def build_value(hier: HierarchyWrapper, arr: np.ndarray, mdatas: t.Sequence):
    if hier.is_empty:
        return arr
    head = hier.head()
    tail = hier.tail()
    generator = (build_value(tail, x, mdatas[1:]) for x in arr)
    return {
        boxes.Tuple: lambda it: tuple(it if arr.size else []),
        boxes.List: lambda it: list(it if arr.size else []),
        SingleItemDict: lambda it: {head.mdata: next(it)},
        MultiItemsDict: lambda it: dict(zip(head.mdata, it)),
        VariadicDict: lambda it: dict(zip(mdatas[0] if arr.size else [], it)),
    }[head.boxtype](generator)


def build_test_pair(
    hier: Hierarchy,
    perm: t.Tuple[int],
    zero_dim: t.Optional[int] = None,
):
    hier = HierarchyWrapper.new(hier)
    dims = []
    mdatas = []
    for node in hier:
        boxtype = node.boxtype
        mdata = {
            VariadicDict: lambda: np.random.randint(
                0, 1 << 31, size=(np.random.randint(1, 11))
            )
        }.get(boxtype, lambda: None)()
        dim = {
            boxes.Tuple: lambda: np.random.randint(1, 11),
            boxes.List: lambda: np.random.randint(1, 11),
            SingleItemDict: lambda: 1,
            MultiItemsDict: lambda: len(node.mdata),
            VariadicDict: lambda: len(mdata),
        }[boxtype]()
        mdatas.append(mdata)
        dims.append(dim)

    if zero_dim is not None:
        dims[zero_dim] = 0

    arr = np.random.randn(*dims)
    ret = build_value(hier, arr, mdatas)
    perm_arr = arr.transpose(perm)
    perm_hier = HierarchyWrapper.new([hier[i] for i in perm])
    perm_mdatas = [mdatas[i] for i in perm]
    perm_ret = build_value(perm_hier, perm_arr, perm_mdatas)

    return ret, perm_ret


PARAMETERS = []
for hier in HIER_CANDIDATES:
    hier = create_hierarchy_nocheck(hier)
    for times in range(N_TEST_TIMES):
        for perm in list(permutations(range(len(hier)))):
            for check in [True, False]:
                for zero_dim in [None] + [
                    i
                    for i in range(len(hier))
                    if hier[i].orig_boxtype is not boxes.Dict
                ]:
                    PARAMETERS.append((hier, perm, check, zero_dim, times))


@pytest.mark.parametrize("hier, perm, check, zero_dim, times_", PARAMETERS)
def test_transforms(
    hier: Hierarchy,
    perm: t.Tuple[int, ...],
    check: bool,
    zero_dim: int,
    times_: int,
):
    x, perm_x = build_test_pair(hier, perm, zero_dim=zero_dim)
    out = ops.transform(hier, perm=perm, check=check)(x)
    assert out == perm_x
