import typing as t

from .shaping import ShapeNode
from .boxmeta import BoxBaseMeta
from .interfaces import Primitives as Primitives_, Heuristics as Heuristics_

class BoxBase(metaclass=BoxBaseMeta):
    Primitives: t.ClassVar[Primitives_]
    Heuristics: t.ClassVar[Heuristics_]
    def __class_getitem__(cls, arg) -> ShapeNode: ...
    @classmethod
    def __guess__(cls, val) -> ShapeNode: ...
    @classmethod
    def __pick_element__(cls, val): ...
    @classmethod
    def __specialize__(cls, arg): ...
    @classmethod
    def __prepare_constants__(cls, mdata): ...
