from hako.bricks.boxbase import BoxBase


class List(BoxBase):
    @classmethod
    def __guess__(cls, v):
        return List

    @classmethod
    def __pick_element__(cls, v):
        return v[0]


List.Primitives.ISNOTA("({VAL}.__class__ is not list)")
List.Primitives.ITER("iter({VAL})")
List.Primitives.NEW_FROM_ITER("(list({VAL}))")
List.Primitives.NEW("[{VAL},]")
List.Primitives.GET_INDICES("range(len({VAL}))")
List.Primitives.GET_DUMMY("[]")
List.Primitives.PICK("{VAL}[0]")
List.Primitives.GET_LENGTH("len({VAL})")

List.Heuristics.IS_NAIVE_ITERATOR(True)
