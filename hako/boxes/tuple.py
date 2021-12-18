from hako.bricks.boxbase import BoxBase


class Tuple(BoxBase):
    @classmethod
    def __guess__(cls, v):
        return Tuple

    @classmethod
    def __pick_element__(cls, v):
        return v[0]


Tuple.Primitives.ISNOTA("({VAL}.__class__ is not tuple)")
Tuple.Primitives.ITER("iter({VAL})")
Tuple.Primitives.NEW_FROM_ITER("(tuple({VAL}))")
Tuple.Primitives.NEW("({VAL},)")
Tuple.Primitives.GET_INDICES("range(len({VAL}))")
Tuple.Primitives.GET_DUMMY("()")
Tuple.Primitives.PICK("{VAL}[0]")
Tuple.Primitives.GET_LENGTH("len({VAL})")

Tuple.Heuristics.IS_NAIVE_ITERATOR(True)
