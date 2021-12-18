PRIMITIVE_ENTRIES = (
    "ISNOTA",
    "ISNOTA2",
    "ISNOTA2_PROOF",
    "ITER",
    "ITER2",
    "ITER2_PROOF",
    "NEW",
    "NEW_FROM_ITER",
    "NEW_FROM_ITER2",
    "NEW_FROM_ITER2_PROOF",
    "GET_INDICES",
    "GET_DUMMY",
    "GET_ITEM",
    "PICK",
    "GET_LENGTH",
    "GET_LENGTH2",
    "GET_LENGTH2_PROOF",
)


class Primitives(dict):
    __slots__ = ("_Heuristics",)

    def __init__(self, heuristics: "Heuristics"):
        for entry in PRIMITIVE_ENTRIES:
            self[entry] = None

        self["GET_ITEM"] = "{VAL}[{INDEX}]"
        self._Heuristics = heuristics

    def _make_declarer(name: str):
        if name.endswith("_PROOF"):

            def _declarer(self, value):
                for other_name in PROOF_ENTRIES:
                    if other_name == name:
                        continue
                    other_value = self[other_name]
                    if other_value is None or other_value != value:
                        continue
                    self._Heuristics["_SAME_PROOF"] |= {
                        (name, other_name),
                        (other_name, name),
                    }
                self[name] = value

        else:

            def _declarer(self, value):
                self[name] = value

        return _declarer

    for name in PRIMITIVE_ENTRIES:
        locals()[name] = _make_declarer(name)

    del name, _make_declarer


PROOF_ENTRIES = [
    "ISNOTA2_PROOF",
    "ITER2_PROOF",
    "NEW_FROM_ITER2_PROOF",
    "GET_LENGTH2_PROOF",
]

HEURISTIC_ENTRIES = [
    ["IS_NAIVE_ITERATOR", lambda: False],
    ["SHAPE_IMPLIES_LENGTH", lambda: False],
    ["_SAME_PROOF", set],
]


class Heuristics(dict):
    __slots__ = ()

    def __init__(self):
        for entry, default in HEURISTIC_ENTRIES:
            self[entry] = default()

    def _make_declarer(name: str):
        def _declarer(self, value):
            self[name] = value

        return _declarer

    for name, _ in HEURISTIC_ENTRIES:
        locals()[name] = _make_declarer(name)

    del name, _, _make_declarer
