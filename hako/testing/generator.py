import enum
import string
import random
import dataclasses
import typing as t

from hako import boxes
from hako.bricks.shaping import Hierarchy, create_hierarchy


class HierarchyWrapper(list):
    __slots__ = ("is_outermost",)

    def __sub__(self, rhs) -> "HierarchyWrapper":
        self.append(ShapeNode.new(rhs))
        return self

    @property
    def is_empty(self) -> bool:
        return not self

    def head(self) -> "ShapeNode":
        return self[0]

    def tail(self) -> "Hierarchy":
        ret = self.new(self[1:])
        ret.is_outermost = False
        return ret

    @classmethod
    def new(cls, obj) -> "HierarchyWrapper":
        ret = cls(create_hierarchy(obj)[0])
        ret.is_outermost = True
        return ret


class MutationKind(enum.Flag):
    NONE = 0
    HIER = enum.auto()
    LEN = enum.auto()


@dataclasses.dataclass
class Context:
    mutation: MutationKind
    outermost: bool = True

    @property
    def DIFF_HIER(self) -> bool:
        return bool(self.mutation & MutationKind.HIER)

    @property
    def SAME_HIER(self) -> bool:
        return not self.DIFF_HIER

    @property
    def DIFF_LEN(self) -> bool:
        return bool(self.mutation & MutationKind.LEN)

    @property
    def SAME_LEN(self) -> bool:
        return not self.DIFF_LEN


SIMPLE_TYPES = [str, bytes, int, float]
TSimpleValue = t.Union[str, bytes, int, float]
TSimpleValues = t.List[TSimpleValue]

TRet = t.Any
Mutated = bool
TGenerator = t.Callable[[Context], t.Tuple[TRet, Mutated]]
TGenerators = t.List[TGenerator]
TValueMaker = t.Callable[[Context, TGenerators], t.Optional[t.Tuple[TRet, Mutated]]]
TValueMakers = t.List[TValueMaker]


@dataclasses.dataclass
class BuildResult:
    rng: random.Random
    retval: t.Any
    generator: TGenerator

    @classmethod
    def create(
        cls,
        rng: random.Random,
        results: t.List["BuildResult"],
        build_retval: t.Callable,
        makers: TValueMakers,
    ) -> "BuildResult":
        retval = build_retval([(x.retval) for x in results])

        def _build_generator(sub_gens: TGenerators) -> TGenerator:
            def _generator(ctx: Context) -> t.Tuple[TRet, Mutated]:
                nonlocal makers
                makers_ = makers[:]
                rng.shuffle(makers_)

                outermost = ctx.outermost
                if outermost:
                    ctx.outermost = False

                for maker in makers_:
                    ret = maker(ctx, sub_gens)
                    if ret is not None:
                        _, mutated = ret
                        if (
                            outermost
                            and (ctx.DIFF_HIER or ctx.DIFF_LEN)
                            and not mutated
                        ):
                            continue
                        return ret
                else:
                    raise RuntimeError("All gen fns exhausted")

            return _generator

        generator = _build_generator([x.generator for x in results])

        return BuildResult(rng, retval, generator)

    def _generate(self, kind: MutationKind):
        return self.generator(Context(kind))[0]

    def gen_same(self):
        return self._generate(MutationKind.NONE)

    def gen_diff_hier(self):
        return self._generate(MutationKind.HIER)

    def gen_diff_len(self):
        return self._generate(MutationKind.LEN)


def run_gens(ctx: Context, gens: TGenerators) -> t.Tuple[t.List[TRet], t.List[Mutated]]:
    rets = [f(ctx) for f in gens]
    return [x[0] for x in rets], [x[1] for x in rets]


@dataclasses.dataclass
class Generator:
    def __post_init__(self):
        self.rng = random.Random()

    def rand_size(self, *, max=5) -> int:
        return self.rng.randint(0, max)

    def rand_str(self, population=(string.ascii_letters + string.digits) * 100) -> str:
        return "".join(self.rng.sample(population, 16))

    def rand_bytes(self) -> bytes:
        return self.rand_str().encode()

    def rand_int(self) -> int:
        return self.rng.randint(0, 1 << 16)

    def rand_float(self) -> float:
        return float(self.rand_int())

    def rand_simple(self) -> TSimpleValue:
        klass = self.rng.choice(SIMPLE_TYPES)
        return {
            str: self.rand_str,
            bytes: self.rand_bytes,
            float: self.rand_float,
            int: self.rand_int,
        }[klass]()

    def rand_seq(self, L=None) -> TSimpleValues:
        if L is None:
            L = self.rand_size()
        return [self.rand_simple() for _ in range(L)]

    def rand_arbitary(self, exclude=None):
        if self.rng.random() > 0.5:
            return self.rand_simple()

        candidates = [list, tuple, dict, set]
        if exclude is not None:
            candidates.remove(exclude)

        klass = self.rng.choice(candidates)
        L = self.rand_size()
        if klass is dict:
            keys = self.rand_seq(L)
            values = self.rand_seq(L)
            return klass(zip(keys, values))
        else:
            return klass(self.rand_seq(L))

    def _box_result(
        self, hier: HierarchyWrapper, results, build_retval, makers
    ) -> BuildResult:
        exclude = {
            boxes.List: list,
            boxes.Tuple: tuple,
            boxes.Dict: dict,
        }[hier.head().orig_boxtype]

        def _maker(ctx: Context, _: TGenerators):
            if ctx.SAME_HIER:
                return None
            return self.rand_arbitary(exclude=exclude), True

        makers.append(_maker)
        return BuildResult.create(self.rng, results, build_retval, makers)

    def build_simple(self) -> BuildResult:
        return BuildResult(
            self.rng,
            self.rand_simple(),
            lambda _ctx: (self.rand_simple(), False),
        )

    def build_box(self, hier: HierarchyWrapper):
        return {
            boxes.List: self.build_list,
            boxes.Tuple: self.build_tuple,
            boxes.Dict: self.build_dict,
        }[hier.head().orig_boxtype](hier)

    def build_value(self, hier: HierarchyWrapper = None):
        if hier is None:
            return BuildResult(
                self.rng,
                self.rand_arbitary(),
                [lambda ctx: (self.rand_arbitary(), False)],
            )
        hier = HierarchyWrapper.new(hier)
        if hier.is_empty:
            return self.build_simple()
        return self.build_box(hier)

    def build_list(self, hier: HierarchyWrapper) -> BuildResult:
        L = self.rand_size()
        results = [self.build_value(hier.tail()) for _ in range(L)]

        def _same_len_maker(ctx: Context, fns: TGenerators):
            vals, mutateds = run_gens(ctx, fns)
            if ctx.DIFF_LEN or ctx.DIFF_HIER:
                mutated = any(mutateds)
            else:
                mutated = False

            return vals, mutated

        def _shorter_len_maker(ctx: Context, fns: TGenerators):
            if ctx.SAME_LEN:
                return None
            vals, mutateds = run_gens(ctx, fns)
            if len(vals) == 0:
                return None

            try:
                i = mutateds.index(False)
            except ValueError:
                i = 0

            del vals[i], mutateds[i]

            if ctx.DIFF_HIER:
                mutated = any(mutateds)
            else:
                mutated = True

            return vals, mutated

        def _longer_len_maker(ctx: Context, fns: TGenerators):
            if ctx.SAME_LEN:
                return None
            fns = fns + [self.build_value(hier.tail()).generator]
            vals, mutateds = run_gens(ctx, fns)

            if ctx.DIFF_HIER:
                mutated = any(mutateds)
            else:
                mutated = True

            return vals, mutated

        return self._box_result(
            hier,
            results,
            list,
            [_same_len_maker, _shorter_len_maker, _longer_len_maker],
        )

    def build_tuple(self, hier: HierarchyWrapper) -> BuildResult:
        L = self.rand_size()
        results = [self.build_value(hier.tail()) for _ in range(L)]

        def _same_len_maker(ctx: Context, fns: TGenerators):
            vals, mutateds = run_gens(ctx, fns)
            if ctx.DIFF_LEN or ctx.DIFF_HIER:
                mutated = any(mutateds)
            else:
                mutated = False

            return tuple(vals), mutated

        def _shorter_len_maker(ctx: Context, fns: TGenerators):
            if ctx.SAME_LEN:
                return None
            vals, mutateds = run_gens(ctx, fns)
            if len(vals) == 0:
                return None

            try:
                i = mutateds.index(False)
            except ValueError:
                i = 0

            del vals[i], mutateds[i]

            if ctx.DIFF_HIER:
                mutated = any(mutateds)
            else:
                mutated = True

            return tuple(vals), mutated

        def _longer_len_maker(ctx: Context, fns: TGenerators):
            if ctx.SAME_LEN:
                return None
            fns = fns + [self.build_value(hier.tail()).generator]
            vals, mutateds = run_gens(ctx, fns)

            if ctx.DIFF_HIER:
                mutated = any(mutateds)
            else:
                mutated = True

            return tuple(vals), mutated

        return self._box_result(
            hier,
            results,
            tuple,
            [_same_len_maker, _shorter_len_maker, _longer_len_maker],
        )

    def build_dict(self, hier: HierarchyWrapper) -> BuildResult:
        mdata = hier.head().mdata
        if mdata is None:
            keys = self.rand_seq()
            if hier.is_outermost:
                # don't generate empty dict, from which we cannot construct diff len values
                keys.append(self.rand_simple())
        elif isinstance(mdata, (list, tuple)):
            keys = list(mdata)
        else:
            keys = [mdata]

        results = [self.build_value(hier.tail()) for _ in keys]

        def _same_len_maker(ctx: Context, fns: TGenerators):
            vals, mutateds = run_gens(ctx, fns)
            if ctx.DIFF_LEN or ctx.DIFF_HIER:
                mutated = any(mutateds)
            else:
                mutated = False
            return dict(zip(keys, vals)), mutated

        def _shorter_len_maker(ctx: Context, fns: TGenerators):
            if ctx.SAME_LEN:
                return None
            vals, mutateds = run_gens(ctx, fns)
            if len(vals) == 0:
                return None
            keys_ = keys[:]

            try:
                i = mutateds.index(False)
            except ValueError:
                i = 0

            del keys_[i], vals[i], mutateds[i]

            if ctx.DIFF_HIER:
                mutated = any(mutateds)
            else:
                mutated = True

            return dict(zip(keys_, vals)), mutated

        def _longer_len_maker(ctx: Context, fns: TGenerators):
            fns = fns + [self.build_value(hier.tail()).generator]
            vals, mutateds = run_gens(ctx, fns)

            if ctx.DIFF_HIER:
                mutated = any(mutateds[:-1])
            else:
                mutated = False

            extra_key = self.rand_simple()
            return dict(zip(keys + [extra_key], vals)), mutated

        return self._box_result(
            hier,
            results,
            lambda vs: dict(zip(keys, vs)),
            [_same_len_maker, _shorter_len_maker, _longer_len_maker],
        )


if __name__ == "__main__":
    gen = Generator()
    result = gen.build_value([boxes.List, boxes.Tuple, boxes.Dict[3]])

    import functools
    from pprint import pprint as pprint_

    pprint = functools.partial(pprint_, compact=False, Indent=2)

    pprint(result.retval)
    pprint(result.gen_same())
    pprint(result.gen_diff_len())
    pprint(result.gen_diff_hier())
