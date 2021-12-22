import typing as t
from random import Random
from linecache import lazycache

from hako.misc.functional import zip_strict
from hako.misc.exceptions import BoxMismatched

from .snippets import *

_BUILTIN_CONSTANTS: t.Dict[str, t.Any] = dict(
    zip_strict=zip_strict,
    len=len,
    zip=zip,
    map=map,
    iter=iter,
    tuple=tuple,
    list=list,
    dict=dict,
    range=range,
    next=next,
    all=all,
    any=any,
    enumerate=enumerate,
    BoxMismatched=BoxMismatched,
    __builtins__={},
)


def register_constants(**ldict: dict):
    _BUILTIN_CONSTANTS.update(ldict)


class _FakeLoader:
    __slots__ = ("lines",)

    def __init__(self, lines: str):
        self.lines = lines

    def get_source(self, name: str) -> str:
        return self.lines


getrandbits = Random(42).getrandbits


def make_func(name, func_sig, func_body, constants):
    constants.update(_BUILTIN_CONSTANTS)
    wrapper_sig = ", ".join(f"{name}={name}" for name in constants)
    source = (
        f"def __WRAPPER__({wrapper_sig}):\n"
        f"{CODE_INDENT_1}def {name}({func_sig}):"
        f"{func_body}\n"
        f"{CODE_INDENT_1}return {name}"
    )
    filename = f"hako::codegen::{getrandbits(32):08x}"
    lazycache(filename, {"__name__": filename, "__loader__": _FakeLoader(source)})

    code = compile(source, filename, "exec")
    exec(code, constants)
    return constants["__WRAPPER__"]()
