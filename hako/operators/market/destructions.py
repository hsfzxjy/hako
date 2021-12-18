from hako.codegen import CodeBuilder
from hako.operators.bases import VariadicOperator

__all__ = ["map", "visit", "flatten"]


def template_map_with_single_arg(
    hier,
    func_name,
    signature,
    yield_statement,
    postproc="",
    check=True,
):
    CB = CodeBuilder(*signature)
    GRs, ST = CB.Setup(hier)

    if postproc:
        CB.Push("def __GEN__():")
        CB.Indent()

    for GR in GRs:
        if check:
            CB.Push(
                f"if {GR.CODE_ISNOTA()}:{{NL}}"
                f'{{>>}}raise BoxMismatched(f"'
                "ARG has unexpected shape\\n"
                "ARG: {{{VAL}!r}}\\n"
                f"SHAPE: {GR.Node!r}"
                '")'
            )
        ST.DefineOrOverwrite("LOOP_VAR")
        CB.Push(f"for {{LOOP_VAR}} in {GR.CODE_ITER_AUTO()}:")
        CB.Indent()
        ST.Alias("LOOP_VAR", "VAL")
    CB.Push(yield_statement)

    if postproc:
        CB.DedentToFront()
        CB.Push(postproc)

    return CB.End(func_name)


def template_map_with_multi_arg(
    hier,
    func_name,
    signature,
    yield_statement,
    postproc="",
    check=True,
):
    CB = CodeBuilder(*signature)
    GRs, ST = CB.Setup(hier)

    if postproc:
        CB.Push("def __GEN__():")
        CB.Indent()

    ST.Define("VAL")
    for GR in GRs:
        if check:
            CB.Push("{VAL} = {VALS}[0]")
            CB.Push(
                f"if {GR.CODE_ISNOTA()}:{{NL}}"
                f'{{>>}}raise BoxMismatched(f"'
                f"0-th ARG has unexpected shape\\n"
                "0-th ARG: {{{VAL}!r}}\\n"
                f"SHAPE: {GR.Node!r}"
                '")'
            )

            GR.Define_LENGTH_REF()
            GR.Define_ISNOTA2_PROOF()

            CB.Push(
                "for I, {VAL} in enumerate({VALS}[1:], start=1):{NL}"
                f"{{>>}}if {GR.CODE_ISNOTA2_AUTO()}:{{NL}}"
                f'{{>>}}{{>>}}raise BoxMismatched(f"'
                "{{I}}-th ARG has unexpected shape\\n"
                "{{I}}-th ARG: {{{VAL}!r}}\\n"
                f"SHAPE: {GR.Node!r}\\n"
                '")',
            )

            CB.Push(
                f"{{>>}}if {GR.CODE_LENGTH_MISMATCHED_AUTO()}:{{NL}}"
                f'{{>>}}{{>>}}raise BoxMismatched(f"'
                "{{I}}-th ARG has different length than 0-th ARG\\n"
                "0-th ARG: {{{VALS}[0]!r}}\\n"
                "{{I}}-th ARG: {{{VAL}!r}}\\n"
                f"SHAPE: {GR.Node!r}\\n"
                # "PROOF: {{{PROOF}!r}}"
                '")',
            )

        ST.DefineOrOverwrite("LOOP_VAR")
        GR.Define_ITER2_PROOF(setup="{VAL} = {VALS}[0]")
        CB.Push(f"for {{LOOP_VAR}} in {GR.CODE_ITER2_ZIP_AUTO()}:")
        CB.Indent()
        ST.Alias("LOOP_VAR", "VALS")

        GR.ResetProofPool()
    CB.Push(yield_statement)

    if postproc:
        CB.DedentToFront()
        CB.Push(postproc)

    return CB.End(func_name)


map = VariadicOperator(
    "map",
    value_arg_idx=1,
    guessable=True,
    extra_operator_sig="lazy=True, check=True, ",
    extra_operator_args="lazy, check",
)


@map.build_func_at_single_arg
def map_single(hier, lazy, check):
    return template_map_with_single_arg(
        hier,
        "map_",
        (["FUNC", "VAL"], None, None),
        "yield {FUNC}({VAL})",
        "" if lazy else "return list(__GEN__())",
        check,
    )


@map.build_func_at_multi_arg
def map_multi(hier, lazy, check):
    return template_map_with_multi_arg(
        hier,
        "map_",
        (["FUNC"], "VALS", None),
        "yield {FUNC}(*{VALS})",
        "" if lazy else "return list(__GEN__())",
        check,
    )


map = map.compile()


visit = VariadicOperator(
    "visit",
    value_arg_idx=1,
    guessable=True,
    extra_operator_sig="check=True, ",
    extra_operator_args="check",
)


@visit.build_func_at_single_arg
def visit_single(hier, check):
    return template_map_with_single_arg(
        hier,
        "visit",
        (["FUNC", "VAL"], None, None),
        "{FUNC}({VAL})",
        "",
        check,
    )


@visit.build_func_at_multi_arg
def visit_multi(hier, check):
    return template_map_with_multi_arg(
        hier,
        "visit",
        (["FUNC"], "VALS", None),
        "{FUNC}(*{VALS})",
        "",
        check,
    )


visit = visit.compile()


flatten = VariadicOperator(
    "flatten",
    value_arg_idx=0,
    guessable=True,
    extra_operator_sig="lazy=True, check=True, ",
    extra_operator_args="lazy, check",
)


@flatten.build_func_at_single_arg
def flatten_single(hier, lazy, check):
    return template_map_with_single_arg(
        hier,
        "flatten",
        (["VAL"], None, None),
        "yield {VAL}",
        "" if lazy else "return list(__GEN__())",
        check,
    )


@flatten.build_func_at_multi_arg
def flatten_multi(hier, lazy, check):
    return template_map_with_multi_arg(
        hier,
        "flatten",
        ([], "VALS", None),
        "yield {VALS}",
        "" if lazy else "return list(__GEN__())",
        check,
    )


flatten = flatten.compile()
