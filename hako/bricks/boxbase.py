import typing as t

from .shaping import ShapeNode
from .interfaces import Primitives, Heuristics


from .boxmeta import BoxBaseMeta


class BoxBase(metaclass=BoxBaseMeta):
    def __class_getitem__(cls, arg):
        scls, arg = cls.__specialize__(arg)
        return ShapeNode(cls, scls, arg, None)

    def __init_subclass__(cls) -> None:
        cls.Heuristics = Heuristics()
        cls.Primitives = Primitives(cls.Heuristics)

    @classmethod
    def __specialize__(cls, arg):
        return cls, arg

    @classmethod
    def __prepare_constants__(cls, mdata):
        return dict(MDATA=mdata)

    @classmethod
    def __guess__(cls, val) -> ShapeNode:
        return cls[None]

    @classmethod
    def __pick_element__(cls, val):
        ...
