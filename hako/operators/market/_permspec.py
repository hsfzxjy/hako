import re
import typing as t
from collections import namedtuple

from hako.bricks.shaping import Hierarchy

__all__ = [
    "parse_permspec",
    "find_cycles",
    "PermSpec",
    "SWAP",
    "REBUILD",
]

PermEq = str
PermSpec = t.Tuple[int, ...]
RE_EQ = re.compile(r"^([a-z]+)\s*->\s*([a-z]+)$")


def parse_permspec(spec: t.Union[PermSpec, PermEq]) -> PermSpec:
    type_ = spec.__class__
    if type_ is str:
        matched = RE_EQ.match(spec)
        if not matched:
            raise RuntimeError
        lhs, rhs = matched.groups()
        mapping = {c: i for i, c in enumerate(lhs)}
        return tuple(mapping[c] for c in rhs)
    elif type_ is tuple:
        depth = max(spec) + 1
        ret = list(range(depth))
        for i, j in enumerate(sorted(spec)):
            ret[j] = spec[i]
        return tuple(ret)
    else:
        raise RuntimeError


Cycle = namedtuple("Cycle", "kind perm local_perm range is_last")

SWAP = 1
REBUILD = 2


def find_cycles(spec: PermSpec, hier: Hierarchy) -> t.Tuple[t.Sequence[Cycle], int]:
    cycles = []

    def _append(kind: int, left: int, right: int):
        sub_perm = spec[left:right]
        cycles.append(
            Cycle(
                kind,
                sub_perm,
                [x - left for x in sub_perm],
                range(left, right),
                right == length,
            )
        )

    ptr = len(spec) - 1
    while ptr >= 0 and spec[ptr] == ptr and hier[ptr].target is None:
        ptr -= 1
    length = ptr + 1
    if ptr > 0 and spec[ptr - 1] == ptr and spec[ptr] == ptr - 1:
        _append(SWAP, ptr - 1, ptr + 1)
        ptr -= 2

    while ptr >= 0:
        highest = ptr
        lowest = spec[ptr]
        if 0 < lowest < highest:
            for ptr in range(ptr - 1, -1, -1):
                v = spec[ptr]
                if v < lowest:
                    lowest = v
                if ptr == lowest:
                    break

        _append(REBUILD, lowest, highest + 1)
        ptr = lowest - 1
    cycles = cycles[::-1]
    return cycles, length
