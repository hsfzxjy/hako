from hako.bricks.boxbase import BoxBase
from hako.codegen import register_constants


class Dict(BoxBase):
    @classmethod
    def __specialize__(cls, arg):
        if arg is None:
            return VariadicDict, arg
        elif arg.__class__ in {tuple, list}:
            arg = list(arg)
            return MultiItemsDict, arg
        else:
            return SingleItemDict, arg

    @classmethod
    def __guess__(cls, v):
        return Dict[list(v)]

    @classmethod
    def __pick_element__(cls, v):
        return next(iter(v.values()))


register_constants(
    dict_values=dict.values,
    dict_keys=dict.keys,
)


class VariadicDict(Dict):
    ...


GET_INDICES = "dict_keys({VAL})"
VariadicDict.Primitives.ISNOTA("({VAL}.__class__ is not dict)")
VariadicDict.Primitives.ISNOTA2(
    "({VAL}.__class__ is not dict or not dict_keys({VAL}) >= {PROOF})"
)
VariadicDict.Primitives.ISNOTA2_PROOF(GET_INDICES)
VariadicDict.Primitives.ITER("dict_values({VAL})")
VariadicDict.Primitives.ITER2("map({VAL}.__getitem__, {PROOF})")
VariadicDict.Primitives.ITER2_PROOF(GET_INDICES)
VariadicDict.Primitives.NEW_FROM_ITER2("dict(zip({PROOF}, {VAL}))")
VariadicDict.Primitives.NEW_FROM_ITER2_PROOF(GET_INDICES)
VariadicDict.Primitives.GET_INDICES(GET_INDICES)
VariadicDict.Primitives.GET_DUMMY("{{}}")
VariadicDict.Primitives.PICK("next(iter({VAL}.values()))")
VariadicDict.Primitives.GET_LENGTH("len({VAL})")

VariadicDict.Heuristics.SHAPE_IMPLIES_LENGTH(True)


class SingleItemDict(Dict):
    @classmethod
    def __prepare_constants__(cls, mdata):
        return dict(MDATA=mdata, MDATA_TUPLE=(mdata,))


SingleItemDict.Primitives.ISNOTA(
    "({VAL}.__class__ is not dict or {MDATA} not in {VAL})"
)
SingleItemDict.Primitives.ITER("({VAL}[{MDATA}],)")
SingleItemDict.Primitives.NEW("{{{MDATA}: {VAL}}}")
SingleItemDict.Primitives.NEW_FROM_ITER("dict(zip({MDATA_TUPLE}, {VAL}))")
SingleItemDict.Primitives.GET_INDICES("{MDATA_TUPLE}")
SingleItemDict.Primitives.GET_DUMMY("{{{MDATA}: ...}}")
SingleItemDict.Primitives.PICK("{VAL}[{MDATA}]")
SingleItemDict.Primitives.GET_LENGTH("1")


SingleItemDict.Heuristics.SHAPE_IMPLIES_LENGTH(True)


class MultiItemsDict(Dict):
    @classmethod
    def __prepare_constants__(cls, mdata):
        return dict(MDATA=mdata, MDATA_SET=frozenset(mdata), MDATA_LENGTH=len(mdata))


MultiItemsDict.Primitives.ISNOTA(
    "({VAL}.__class__ is not dict or not dict_keys({VAL}) >= {MDATA_SET})"
)
MultiItemsDict.Primitives.ITER("map({VAL}.__getitem__, {MDATA})")
MultiItemsDict.Primitives.NEW_FROM_ITER("dict(zip({MDATA}, {VAL}))")
MultiItemsDict.Primitives.GET_INDICES("{MDATA}")
MultiItemsDict.Primitives.GET_DUMMY("{{I: ... for I in {MDATA}}}")
MultiItemsDict.Primitives.PICK("{VAL}[{MDATA}[0]]")
MultiItemsDict.Primitives.GET_LENGTH("{MDATA_LENGTH}")

MultiItemsDict.Heuristics.SHAPE_IMPLIES_LENGTH(True)
