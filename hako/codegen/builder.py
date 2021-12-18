import typing as t

import random

from .grocery import SnippetGrocery
from .magic import make_func
from .snippets import *

VariableName = str
Symbol = str
Symbol2VariableNameMapping = t.Mapping[Symbol, VariableName]
SrcSymbol = Symbol
DstSymbol = Symbol
SymbolAliasMapping = t.Mapping[DstSymbol, SrcSymbol]


class SymbolHolder:
    __slots__ = "_dict", "_var_counter"

    def __init__(self, s2vn: Symbol2VariableNameMapping) -> None:
        self._dict = s2vn
        self._var_counter = 0

    def _new_variable_name(self) -> VariableName:
        varname = f"X{self._var_counter}"
        self._var_counter += 1
        return varname

    def Define(self, sym: Symbol) -> VariableName:
        if sym in self._dict:
            raise KeyError(sym)
        name = self._new_variable_name()
        self._dict[sym] = name
        return name

    def DefineOrOverwrite(self, sym: Symbol) -> VariableName:
        name = self._new_variable_name()
        self._dict[sym] = name
        return name

    def Alias(self, sym: SrcSymbol, sym2: DstSymbol):
        if sym not in self._dict:
            return
        self._dict[sym2] = self._dict[sym]

    def AliasMap(self, mapping: SymbolAliasMapping):
        for dst, src in mapping.items():
            self._dict[dst] = self._dict[src]

    def NewSymbol(self, *, getrandbits=random.getrandbits) -> Symbol:
        return f"SYM_{getrandbits(32)}"

    def NewDefinedSymbol(self) -> Symbol:
        sym = self.NewSymbol()
        self.Define(sym)
        return sym

    def SymbolDefined(self, sym: Symbol) -> bool:
        return sym in self._dict


class CodeBuilder:
    def __init__(self, *param_spec: t.List[str]) -> None:
        self._indent_level = 2
        self._codes = []

        self._s2vn: Symbol2VariableNameMapping = {
            "CODE_INDENT_1": CODE_INDENT_1,
            "CODE_INDENT_2": CODE_INDENT_2,
            "NL": "\n" + CODE_INDENT_2,
            ">>": CODE_INDENT_1,
        }
        self._constants = {}
        self.ST = ST = SymbolHolder(self._s2vn)

        parameters = []
        for sym in param_spec[0]:
            parameters.append(ST.Define(sym))
        vararg = param_spec[1]
        if vararg:
            parameters.append("*" + ST.Define(vararg))
        kwarg = param_spec[2]
        if kwarg:
            parameters.append("*" + ST.Define(kwarg))
        self._parameters = ", ".join(parameters)

    def Setup(self, hier) -> t.Tuple[t.Sequence[SnippetGrocery], SymbolHolder]:
        groceries: t.Sequence[SnippetGrocery] = []
        for node in hier:
            GR = SnippetGrocery(node, self)
            groceries.append(GR)

        return groceries, self.ST

    def Dedent(self, level=1) -> None:
        self._indent_level -= level
        self._s2vn["NL"] = "\n" + CODE_INDENT_1 * self._indent_level

    def DedentToFront(self) -> None:
        self._indent_level = 2
        self._s2vn["NL"] = "\n" + CODE_INDENT_2

    def Indent(self) -> None:
        self._indent_level += 1
        self._s2vn["NL"] += CODE_INDENT_1

    def BindConstant(self, sym: Symbol, value):
        self._constants[self._s2vn[sym]] = value
        return self

    def Push(self, snippet: str, **symbol_aliases: SrcSymbol):
        if not snippet:
            return

        s2vn = self._s2vn
        if symbol_aliases:
            for SYM_DST, SYM_SRC in symbol_aliases.items():
                if SYM_SRC not in s2vn:
                    continue
                s2vn[SYM_DST] = s2vn[SYM_SRC]

        codes = self._codes
        snippet = snippet.format_map(s2vn)
        codes.extend([s2vn["NL"], snippet])

    def End(self, name) -> t.Callable:
        return make_func(
            name,
            self._parameters,
            "".join(self._codes),
            self._constants,
        )
