import pytest

from hako import boxes as b
from hako.bricks.shaping import SHAPENODE_PLACEHOLDER, create_hierarchy_nocheck

PARAMETERS = [
    [
        tuple,
        [b.Tuple[None]],
    ],
    [
        (tuple,),
        [b.Tuple[None]],
    ],
    [
        b.Tuple,
        [b.Tuple[None]],
    ],
    [
        b.Tuple - list,
        [b.Tuple[None], b.List[None]],
    ],
    [
        tuple - b.List,
        [b.Tuple[None], b.List[None]],
    ],
    [
        b.Tuple - list - b.Dict,
        [b.Tuple[None], b.List[None], b.Dict[None]],
    ],
    [
        b.Tuple / b.Dict - list - b.Dict,
        [b.Tuple[None]._replace(target=b.Dict[None]), b.List[None], b.Dict[None]],
    ],
    [
        b.Tuple - list / b.Dict - b.Dict,
        [b.Tuple[None], b.List[None]._replace(target=b.Dict[None]), b.Dict[None]],
    ],
    [
        b.Tuple - list - b.Dict / b.Dict,
        [b.Tuple[None], b.List[None], b.Dict[None]._replace(target=b.Dict[None])],
    ],
    # with placeholder
    [
        ...,
        [SHAPENODE_PLACEHOLDER],
    ],
    [
        ... - b.Tuple,
        [SHAPENODE_PLACEHOLDER, b.Tuple[None]],
    ],
    [
        b.Tuple - ...,
        [b.Tuple[None], SHAPENODE_PLACEHOLDER],
    ],
    [
        ... / b.Tuple,
        [SHAPENODE_PLACEHOLDER / b.Tuple[None]],
    ],
    [
        ... / b.Tuple - b.List,
        [SHAPENODE_PLACEHOLDER / b.Tuple[None], b.List[None]],
    ],
    [
        b.List - ... / b.Tuple,
        [b.List[None], SHAPENODE_PLACEHOLDER / b.Tuple[None]],
    ],
]


@pytest.mark.parametrize("expr, result", PARAMETERS)
def test_arithemics(expr, result):
    assert create_hierarchy_nocheck(expr) == tuple(result)
