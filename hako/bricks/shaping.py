import typing as t
from collections import namedtuple
from collections.abc import Sequence

from .boxmeta import BoxBaseMeta


class ShapeNode(
    namedtuple("ShapeNode", ["orig_boxtype", "boxtype", "mdata", "target"])
):
    __slots__ = ()

    def __truediv__(self, rhs) -> "ShapeNode":
        if rhs is ...:
            raise ValueError
        if self.target is not None:
            raise ValueError
        return self._replace(target=self.new(rhs))

    def __rtruediv__(self, lhs) -> "ShapeNode":
        lhs = self.new(lhs)
        return lhs._replace(target=self)

    def __sub__(self, rhs) -> "Hierarchy":
        return (self, rhs)

    def __rsub__(self, lhs) -> "Hierarchy":
        if lhs.__class__ is tuple:
            lhs += (self,)
            return lhs
        return (lhs, self)

    def __repr__(self) -> str:
        repr_string = f"{self.boxtype.__name__}[{self.mdata!r}]"
        if self.target is not None:
            repr_string += f" / {self.target!r}"

        return repr_string

    @property
    def is_placeholder(self) -> bool:
        return self.orig_boxtype is None

    @classmethod
    def new(cls, obj) -> "ShapeNode":
        if obj is ...:
            return SHAPENODE_PLACEHOLDER
        if obj.__class__ is cls:
            return obj

        if isinstance(obj, BoxBaseMeta):
            return obj[None]

        if obj in CLASS2BOXTYPE_MAPPING:
            return CLASS2BOXTYPE_MAPPING[obj][None]

        raise RuntimeError


SHAPENODE_PLACEHOLDER = ShapeNode(None, None, None, None)

from hako.boxes._registries import CLASS2BOXTYPE_MAPPING

PartialHierarchy = Hierarchy = t.Tuple[ShapeNode, ...]


def create_hierarchy(obj):
    if (
        isinstance(obj, (BoxBaseMeta, ShapeNode))
        or obj is ...
        or isinstance(obj, type)
        and obj in CLASS2BOXTYPE_MAPPING
    ):
        obj = (obj,)

    if obj.__class__ is not tuple:
        raise TypeError

    ret = []
    determined = True
    for x in obj:
        if x is ...:
            determined = False
        x = ShapeNode.new(x)
        ret.append(x)
    return tuple(ret), determined


def create_hierarchy_nocheck(obj):
    if (
        isinstance(obj, (BoxBaseMeta, ShapeNode))
        or obj is ...
        or isinstance(obj, type)
        and obj in CLASS2BOXTYPE_MAPPING
    ):
        obj = (obj,)

    if obj.__class__ is not tuple:
        raise TypeError

    return tuple(map(ShapeNode.new, obj))


def guess_hierarchy(
    val,
    partial_hier: PartialHierarchy,
    depth: t.Optional[int],
) -> Hierarchy:
    hier = []
    if depth is not None:
        while depth > 0:
            class_ = val.__class__
            if class_ not in CLASS2BOXTYPE_MAPPING:
                raise ValueError
            boxtype = CLASS2BOXTYPE_MAPPING[class_]
            node = boxtype.__guess__(val)
            val = boxtype.__pick_element__(val)
            depth -= 1
            hier.append(node)
    else:
        for node in partial_hier:
            if node.is_placeholder:
                class_ = val.__class__
                if class_ not in CLASS2BOXTYPE_MAPPING:
                    raise ValueError
                boxtype = CLASS2BOXTYPE_MAPPING[class_]
                node = boxtype.__guess__(val)._replace(target=node.target)
            val = boxtype.__pick_element__(val)
    return tuple(hier)
