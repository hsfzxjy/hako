import typing as t

PRIMITIVE_ENTRIES: t.List[str]
HEURISTIC_ENTRIES: t.List[t.Tuple[str, t.Any]]

V = t.TypeVar("V", str, t.Callable[[t.Any], str])

class Primitives(dict):
    def ISNOTA(self, value: V) -> V: ...
    def ISNOTA2(self, value: V) -> V: ...
    def ISNOTA2_PROOF(self, value: V) -> V: ...
    def ITER(self, value: V) -> V: ...
    def ITER2(self, value: V) -> V: ...
    def ITER2_PROOF(self, value: V) -> V: ...
    def NEW(self, value: V) -> V: ...
    def NEW_FROM_ITER(self, value: V) -> V: ...
    def NEW_FROM_ITER2(self, value: V) -> V: ...
    def NEW_FROM_ITER2_PROOF(self, value: V) -> V: ...
    def GET_INDICES(self, value: V) -> V: ...
    def GET_DUMMY(self, value: V) -> V: ...
    def GET_ITEM(self, value: V) -> V: ...
    def PICK(self, value: V) -> V: ...
    def GET_LENGTH(self, value: V) -> V: ...
    def GET_LENGTH2(self, value: V) -> V: ...
    def GET_LENGTH2_PROOF(self, value: V) -> V: ...

class Heuristics(dict):
    def IS_NAIVE_ITERATOR(self, value: V) -> None: ...
    def SHAPE_IMPLIES_LENGTH(self, value: V) -> None: ...
