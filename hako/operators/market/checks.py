from hako.codegen import CodeBuilder
from hako.operators.bases import SimpleOperator

__all__ = ["isa"]

isa = SimpleOperator("isa", guessable=False)


@isa.build_func
def isa_build(hier) -> bool:
    CB = CodeBuilder(["VAL"], None, None)
    GRs, ST = CB.Setup(hier)
    last_groc = GRs[-1]

    for GR in GRs:
        CB.Push(f"if {GR.CODE_ISNOTA()}: return False")

        if GR is last_groc:
            break

        ST.DefineOrOverwrite("LOOP_VAR")
        CB.Push(f"for {{LOOP_VAR}} in {GR.CODE_ITER()}:")

        ST.Alias("LOOP_VAR", "VAL")
        CB.Indent()
    CB.DedentToFront()
    CB.Push(f"return True")
    return CB.End("isa")


isa = isa.compile()
