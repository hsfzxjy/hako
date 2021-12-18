from hako.codegen import CodeBuilder
from hako.bricks.shaping import Hierarchy
from hako.operators.bases import SimpleOperator

from ._permspec import *

__all__ = ["transform"]

transform = SimpleOperator(
    "transform",
    guessable=True,
    value_arg_idx=0,
    extra_operator_sig="perm=None, check=True, ",
    extra_operator_args="perm, check, ",
    pre_check_snip="""
    assert hier or depth is not None or perm is not None
    assert not (hier and depth)
    if hier is not None:
        hier, _ = create_hierarchy(hier)
    if perm is None:
        if depth is not None:
            perm = tuple(range(depth))
        elif hier:
            perm = tuple(range(len(hier)))
        else:
            raise ValueError
    else:
        perm = parse_permspec(perm)
        length = len(perm)
        if depth is not None:
            assert depth >= length
        elif hier:
            assert len(hier) >= length
        else:
            depth = length
    """,
    extra_constants=dict(parse_permspec=parse_permspec),
)


@transform.build_func
def transform_build(hier: Hierarchy, permspec: PermSpec, check: bool):
    cycles, length = find_cycles(permspec, hier)
    hier = hier[:length]
    CB = CodeBuilder(["VALUE"], None, None)
    GRs, ST = CB.Setup(hier)

    # operator should be identity when transformation is trivial
    if not cycles:
        CB.Push("return {VALUE}")
        return CB.End("transform")

    # do checking and prepare indices
    ST.Define("VAL")
    CB.Push("{VAL} = {VALUE}")
    ST.Define("EMPTIED")
    CB.Push("{EMPTIED} = False")
    for GR in GRs:
        if GR is not GRs[0]:
            CB.Push(f"{{>>}}{{VAL}} = {GR.CODE_GET_DUMMY()}")

        if check:
            CB.Push(
                f"if {GR.CODE_ISNOTA()}:{{NL}}"
                f'{{>>}}raise BoxMismatched(f"'
                "ARG has unexpected shape\\n"
                "ARG: {{{VAL}!r}}\\n"
                f"SHAPE: {GR.Node!r}"
                '")',
            )

        ST.Define(GR.SYM_INDICES)
        CB.Push(f"{{{GR.SYM_INDICES}}} = {GR.CODE_GET_INDICES()}")
        GR.Define_LENGTH_REF()
        if check:
            GR.Define_ISNOTA2_PROOF()
        GR.Define_ITER2_PROOF()
        GR.Define_NEW_FROM_ITER2_PROOF(
            cond=GR.DEFINED_NEW_FROM_ITER2 and not GR.HasTarget
        )
        CB.Push(
            f"if not {{EMPTIED}} and {GR.CODE_IS_NOT_EMPTY()}:{{NL}}"
            f"{{>>}}{{VAL}} = {GR.CODE_PICK()}"
        )
        if GR is not GRs[-1]:
            CB.Push(f"else:{{NL}}" f"{{>>}}{{EMPTIED}} = True")

    if check:
        CB.Push("{VAL} = {VALUE}")
        for GR in GRs:
            CB.Push(
                f"if {GR.CODE_ISNOTA2_AUTO()}:{{NL}}"
                f'{{>>}}raise BoxMismatched(f"'
                "ARG has unexpected shape\\n"
                "ARG: {{{VAL}!r}}\\n"
                f"SHAPE: {GR.Node!r}"
                '")',
            )
            CB.Push(
                f"if {GR.CODE_LENGTH_MISMATCHED_AUTO()}:{{NL}}"
                f'{{>>}}raise BoxMismatched(f"'
                "ARG has unexpected length\\n"
                "ARG: {{{VAL}!r}}\\n"
                f"SHAPE: {GR.Node!r}\\n"
                # "PROOF: {{{PROOF}!r}}"
                '")',
            )
            if GR is GRs[-1]:
                break

            ST.DefineOrOverwrite("LOOP_VAR")
            CB.Push(f"for {{LOOP_VAR}} in {GR.CODE_ITER2_AUTO()}:")
            CB.Indent()
            ST.Alias("LOOP_VAR", "VAL")
        CB.DedentToFront()

    CB.Push("if {EMPTIED}:")
    CB.Indent()
    deepest = True
    for cycle in reversed(cycles):
        for pindex in reversed(cycle.perm):
            GR = GRs[pindex]
            if deepest:
                ST.DefineOrOverwrite("RET")
                CB.Push(f"{{RET}} = (lambda _: {GR.CODE_GET_DUMMY()})")
            else:
                ST.DefineOrOverwrite("RET_ITER")
                CB.Push(f"{{RET_ITER}} = map({{RET}}, range({{{GR.SYM_LENGTH_REF}}}))")
                ST.DefineOrOverwrite("RET")
                CB.Push(
                    f"{{RET}} = lambda _: {GR.CODE_NEW_FROM_ITER2_AUTO()}",
                    VAL="RET_ITER",
                )
            deepest = False
    CB.Push(f"return {{RET}}(None)")
    CB.Dedent()
    FUNCs = []
    CONs = []

    CONs.append(ST.NewDefinedSymbol())
    CB.Push("{VAL} = {VALUE}", VAL=CONs[-1])
    for cycle in cycles:
        if cycle.kind == REBUILD:
            nFUNC = len(cycle.range)
            CONs.append(ST.NewDefinedSymbol())
        else:
            nFUNC = 1
        for _ in range(nFUNC):
            FUNC = ST.NewDefinedSymbol()
            FUNCs.append(FUNC)
            CB.Push("def {FUNC}():", FUNC=FUNC)
            CB.Indent()

    prev_GR = None
    for cycle in reversed(cycles):
        if cycle.kind == SWAP:
            GR1, GR2 = map(GRs.__getitem__, cycle.range)
            ST.DefineOrOverwrite("TMP")
            CB.Push(
                f"{{TMP}} = {GR1.CODE_ITER2_AUTO()}",
                VAL=CONs[-1],
            )
            CB.Push(
                f"{{TMP}} = ({GR2.CODE_ITER2_AUTO()} for {{VAL}} in {{TMP}})",
                VAL=ST.NewDefinedSymbol(),
            )
            CB.Push(f"{{TMP}} = zip(*{{TMP}})")
            CB.Push(
                f"{{TMP}} = ({GR1.CODE_NEW_FROM_ITER2_AUTO()} for {{VAL}} in {{TMP}})",
                VAL=ST.NewDefinedSymbol(),
            )
            CB.Push(f"return {{TMP}}")
            prev_GR = GR2
            CB.Dedent()
        else:
            INDEXs = [ST.NewDefinedSymbol() for _ in cycle.range]
            is_last_of_cycle = True
            for pindex, lpindex in zip(
                reversed(cycle.perm),
                reversed(cycle.local_perm),
            ):
                CB.Push(f"for {{{INDEXs[lpindex]}}} in {{{GRs[pindex].SYM_INDICES}}}:")
                CB.Indent()

                if is_last_of_cycle:
                    ST.Alias(CONs[-2], "VAL")
                    ST.Alias(CONs[-1], "CUR")
                    for index, ipindex in enumerate(cycle.perm):
                        CB.Push(
                            f"{{CUR}} = {GRs[ipindex].CODE_GET_ITEM()}",
                            INDEX=INDEXs[index],
                        )
                        ST.Alias("CUR", "VAL")

                if is_last_of_cycle and cycle.is_last:
                    CB.Push("yield {CUR}")
                else:
                    ST.DefineOrOverwrite("VAL")
                    CB.Push("{VAL} = {FUNC}()", FUNC=FUNCs[-1])
                    CB.Push(f"yield {prev_GR.CODE_NEW_FROM_ITER2_AUTO()}")
                    FUNCs.pop()

                CB.Dedent()
                CB.Dedent()

                prev_GR = GRs[pindex]
                is_last_of_cycle = False
            CONs.pop()

    ST.DefineOrOverwrite("VAL")
    CB.Push("{VAL} = {FUNC}()", FUNC=FUNCs[-1])
    CB.Push(f"return {prev_GR.CODE_NEW_FROM_ITER2_AUTO()}")

    return CB.End("transform")


transform = transform.compile()
