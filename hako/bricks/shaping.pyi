import typing as t
from hako.bricks.boxbase import BoxBase

class ShapeNode(t.NamedTuple):
    orig_boxtype: t.Type[BoxBase]
    boxtype: t.Type[BoxBase]
    mdata: t.Any
    target: t.Optional[ShapeNode]
    @property
    def is_placeholder(self) -> bool: ...
    @classmethod
    def new(cls, obj) -> ShapeNode: ...

SHAPENODE_PLACEHOLDER: ShapeNode

PartialHierarchy = Hierarchy = t.Sequence[ShapeNode]

def create_hierarchy(
    obj,
) -> t.Union[
    t.Tuple[PartialHierarchy, t.Literal[False]],
    t.Tuple[Hierarchy, t.Literal[True]],
]: ...
def guess_hierarchy(val, depth: int) -> Hierarchy: ...
