import typing as t

from hako.bricks.interfaces import PRIMITIVE_ENTRIES


if t.TYPE_CHECKING:
    from .builder import CodeBuilder, SymbolAliasMapping, Symbol
    from ..bricks.shaping import ShapeNode


class SnippetGrocery:
    def __init__(self, node: "ShapeNode", CB: "CodeBuilder") -> None:
        self.CB = CB
        self.ST = ST = CB.ST
        self.Node = node

        boxtype = node.boxtype
        Primitives = boxtype.Primitives
        Heuristics = boxtype.Heuristics

        target = node.target
        self.HasTarget = target is not None
        self.TargetGrocery = SnippetGrocery(target, CB) if self.HasTarget else None

        self.DEFINED_ISNOTA2 = Primitives["ISNOTA2"] is not None
        self.DEFINED_ITER2 = Primitives["ITER2"] is not None
        self.DEFINED_NEW_FROM_ITER2 = Primitives["NEW_FROM_ITER2"] is not None
        self.DEFINED_GET_LENGTH = Primitives["GET_LENGTH"] is not None
        self.DEFINED_GET_LENGTH2 = Primitives["GET_LENGTH2"] is not None

        self.SYM_INDICES = ST.NewSymbol()
        self.SYM_LENGTH_REF = ST.NewSymbol()
        self.SYM_LENGTH_SELF = ST.NewSymbol()
        self.SYM_SPROOF = ST.NewSymbol()
        self.SYM_IPROOF = ST.NewSymbol()
        self.SYM_GLPROOF = ST.NewSymbol()
        self.SYM_NIPROOF = ST.NewSymbol()

        self._PrimitivesGet = Primitives.__getitem__
        self._HeuristicsGet = Heuristics.__getitem__

        mapping = boxtype.__prepare_constants__(node.mdata)
        for SYM, constant in mapping.items():
            mapping[SYM] = SYM2 = ST.NewDefinedSymbol()
            CB.BindConstant(SYM2, constant)
        self._symbol_alias_mapping: SymbolAliasMapping = mapping

        for key, value in Heuristics.items():
            setattr(self, f"H_{key}", value)

        self._proof_pool = []

    # Helper functions for generating snippets

    def Define_LENGTH_REF(self) -> None:
        ST, CB = self.ST, self.CB
        self.Define_GET_LENGTH2_PROOF()
        if not ST.SymbolDefined(self.SYM_LENGTH_REF):
            ST.Define(self.SYM_LENGTH_REF)

        if self.DEFINED_GET_LENGTH:
            CB.Push(f"{{{self.SYM_LENGTH_REF}}} = {self.CODE_GET_LENGTH()}")
        elif ST.SymbolDefined(self.SYM_INDICES):
            CB.Push(f"{{{self.SYM_LENGTH_REF}}} = len({{{self.SYM_INDICES}}})")

    def CODE_GET_LENGTH2_AUTO(self) -> str:
        if self.DEFINED_GET_LENGTH2:
            self.ST.Alias(self.SYM_GLPROOF, "PROOF")
            return self.CODE_GET_LENGTH2()
        else:
            return self.CODE_GET_LENGTH()

    def CODE_LENGTH_MISMATCHED_AUTO(self) -> str:
        if self.H_SHAPE_IMPLIES_LENGTH:
            return "False"

        self.ST.Alias(self.SYM_GLPROOF, "PROOF")
        return f"({self.CODE_GET_LENGTH2_AUTO()} != {{{self.SYM_LENGTH_REF}}})"

    def CODE_IS_NOT_EMPTY(self) -> str:
        return f"({{{self.SYM_LENGTH_REF}}})"

    def CODE_ITER_AUTO(self) -> str:
        if self.H_IS_NAIVE_ITERATOR:
            return "{VAL}"
        else:
            return self.CODE_ITER()

    def CODE_ITER2_AUTO(self) -> str:
        if self.H_IS_NAIVE_ITERATOR:
            return "{VAL}"

        if self.DEFINED_ITER2:
            self.ST.Alias(self.SYM_IPROOF, "PROOF")
            CODE_ITER = self.CODE_ITER2()
        else:
            CODE_ITER = self.CODE_ITER()

        return CODE_ITER

    def CODE_ITER2_ZIP_AUTO(self, VALS="VALS") -> str:
        if self.H_IS_NAIVE_ITERATOR:
            return f"zip(*{{{VALS}}})"

        if self.DEFINED_ITER2:
            self.ST.Alias(self.SYM_IPROOF, "PROOF")
            CODE_ITER = self.CODE_ITER2()
        else:
            CODE_ITER = self.CODE_ITER()

        return f"zip(*({CODE_ITER} for {{VAL}} in {{{VALS}}}))"

    def CODE_ISNOTA2_AUTO(self) -> str:
        if self.DEFINED_ISNOTA2:
            self.ST.Alias(self.SYM_SPROOF, "PROOF")
            return self.CODE_ISNOTA2()
        else:
            return self.CODE_ISNOTA()

    def CODE_NEW_FROM_ITER2_AUTO(self) -> str:
        if self.HasTarget:
            self = self.TargetGrocery

        if self.DEFINED_NEW_FROM_ITER2:
            self.ST.Alias(self.SYM_NIPROOF, "PROOF")
            return self.CODE_NEW_FROM_ITER2()
        else:
            return self.CODE_NEW_FROM_ITER()

    # Dummy functions for IntelliSense

    def CODE_ISNOTA(self) -> str:
        ...

    def CODE_ISNOTA2(self) -> str:
        ...

    def CODE_ISNOTA2_PROOF(self) -> str:
        ...

    def CODE_ITER(self) -> str:
        ...

    def CODE_ITER2(self) -> str:
        ...

    def CODE_ITER2_PROOF(self) -> str:
        ...

    def CODE_NEW(self) -> str:
        ...

    def CODE_NEW_FROM_ITER(self) -> str:
        ...

    def CODE_NEW_FROM_ITER2(self) -> str:
        ...

    def CODE_NEW_FROM_ITER2_PROOF(self) -> str:
        ...

    def CODE_GET_INDICES(self) -> str:
        ...

    def CODE_GET_DUMMY(self) -> str:
        ...

    def CODE_GET_ITEM(self) -> str:
        ...

    def CODE_PICK(self) -> str:
        ...

    def CODE_GET_LENGTH(self) -> str:
        ...

    def CODE_GET_LENGTH2(self) -> str:
        ...

    def CODE_GET_LENGTH2_PROOF(self) -> str:
        ...

    # The dirty part: function auto generation

    def _make_code_func(name: str):
        def _code_func(self: "SnippetGrocery") -> str:

            code = self._PrimitivesGet(name)

            if code is None:
                raise NotImplementedError(
                    f"Primitive {name!r} not implemented on BoxType {self.Node!r}"
                )

            self.ST.AliasMap(self._symbol_alias_mapping)

            if code.__class__ is str:
                return code

            return code(self)

        return _code_func

    for name in PRIMITIVE_ENTRIES:
        locals()[f"CODE_{name}"] = _make_code_func(name)

    del _make_code_func, name

    def _make_define_proof(
        name: str,
        default_cond: t.Callable[[t.Any], bool],
        sym_getter: t.Callable[["SnippetGrocery"], "Symbol"],
    ):
        def _define_proof(
            self: "SnippetGrocery",
            cond: bool = None,
            setup: str = None,
        ):
            if cond == False or cond is None and not default_cond(self):
                return

            SYM = sym_getter(self)

            ST = self.ST
            ST.DefineOrOverwrite(SYM)
            if setup is not None:
                self.CB.Push(setup)

            for name2, SYM2 in self._proof_pool:
                if (name, name2) in self.H__SAME_PROOF:
                    self.CB.Push(f"{{{SYM}}} = {{{SYM2}}}")
                    break
            else:
                code = getattr(self, f"CODE_{name}")()
                self.CB.Push(f"{{{SYM}}} = {code}")
            self._proof_pool.append((name, SYM))

        return _define_proof

    Define_ISNOTA2_PROOF = _make_define_proof(
        "ISNOTA2_PROOF",
        lambda self: self.DEFINED_ISNOTA2,
        lambda self: self.SYM_SPROOF,
    )

    Define_ITER2_PROOF = _make_define_proof(
        "ITER2_PROOF",
        lambda self: self.DEFINED_ITER2 and not self.H_IS_NAIVE_ITERATOR,
        lambda self: self.SYM_IPROOF,
    )

    Define_GET_LENGTH2_PROOF = _make_define_proof(
        "GET_LENGTH2_PROOF",
        lambda self: self.DEFINED_GET_LENGTH2,
        lambda self: self.SYM_GLPROOF,
    )

    Define_NEW_FROM_ITER2_PROOF = _make_define_proof(
        "NEW_FROM_ITER2_PROOF",
        lambda self: self.DEFINED_NEW_FROM_ITER2,
        lambda self: self.SYM_NIPROOF,
    )

    del _make_define_proof

    def ResetProofPool(self):
        self._proof_pool.clear()
