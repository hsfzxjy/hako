from hako.codegen import CodeBuilder
from hako.operators.bases import SimpleOperator

__all__ = ["lift"]

lift = SimpleOperator(
    "lift",
    guessable=False,
    extra_operator_sig="fullcheck=True, ",
    extra_operator_args="fullcheck,",
)


@lift.build_func
def lift_into_build(hier, fullcheck):
    CB = CodeBuilder(["VALUE"], None, None)
    GRs, ST = CB.Setup(hier)
    nGR = len(GRs)

    ST.Define("VAL")

    for i in range(0, nGR + 1):
        CB.Push("{VAL} = {VALUE}")
        CB.Push("BROKEN = False")
        CB.Push("while True:")
        CB.Indent()

        if not fullcheck and i != nGR:
            CB.Push("while True:")
            CB.Indent()

        for j in range(i, nGR):
            GRj = GRs[j]

            CB.Push(
                f"if {GRj.CODE_ISNOTA()}:{{NL}}"
                f"{{>>}}BROKEN = True{{NL}}"
                f"{{>>}}break"
            )

            if j == nGR - 1:
                break

            if fullcheck:
                ST.DefineOrOverwrite("LOOP_VAR")
                CB.Push(f"for {{LOOP_VAR}} in {GRj.CODE_ITER_AUTO()}:")
                CB.Indent()
                ST.Alias("LOOP_VAR", "VAL")
            else:
                GRj.Define_LENGTH_REF()
                CB.Push(f"if not {{{GRj.SYM_LENGTH_REF}}}: break")
                CB.Push(f"{{VAL}} = {GRj.CODE_PICK()}")

        if fullcheck:
            for j in range(i, nGR - 1):
                CB.Dedent()
                CB.Push("if BROKEN: break")
        elif i != nGR:
            CB.Push("break")
            CB.Dedent()
            CB.Push("if BROKEN: break")
        CB.Push("{VAL} = {VALUE}")
        for j in reversed(range(i)):
            CB.Push(f"{{VAL}} = {GRs[j].CODE_NEW()}")
        CB.Push("return {VAL}")
        CB.Dedent()

    return CB.End("lift")


lift = lift.compile()
