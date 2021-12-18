import re
from textwrap import dedent
from typing import Callable

from hako.codegen.snippets import CODE_INDENT_1
from hako.codegen.magic import make_func
from hako.bricks.shaping import guess_hierarchy, create_hierarchy


def reindent(code: str, level: int, strip: bool = True):
    leading_indent = re.findall(r"^(?:\s*\n)?( *)", code)[0]

    if strip:
        code = code.strip()

    code_new = code.replace(
        "\n" + leading_indent,
        "\n" + CODE_INDENT_1 * (level),
    )
    return code_new


class OperatorBase:
    def __init__(
        self,
        name,
        guessable=False,
        value_arg_idx=None,
        extra_operator_sig="",
        extra_operator_args="",
        pre_check_snip="",
        extra_constants=None,
        **kwargs,
    ) -> None:
        self._name = name
        self._guessable = guessable
        self._value_arg_idx = value_arg_idx
        self._extra_operator_sig = extra_operator_sig
        self._extra_operator_args = extra_operator_args
        self._extra_constants = extra_constants or {}

        self._pre_check = pre_check_snip
        self.__post_init__(kwargs)

    def _snip_get_func(self, call_args=""):
        ...

    def _snip_body(self):
        snip_get_func = self._snip_get_func()
        snip_get_func_with_args = self._snip_get_func("(*args)")
        if self._guessable:
            snip_body = """
            if hier is not None:
                if depth is not None:
                    raise TypeError("expect depth to be None when hier given")

                hier, determined = create_hierarchy(hier)
            else:
                determined = False
                
            if determined:
                {get_func_level_1}
            else:
                def _func(*args):
                    example = args[value_arg_idx]
                    hier = guess_hierarchy(example, depth)
                    {get_func_with_args_level_2}

                return _func
            """
        else:
            snip_body = """
            hier, determined = create_hierarchy(hier)
            if not determined:
                raise ValueError("hier should not contain placeholder `...`")
            {get_func_level_0}
            """

        ret = dedent(snip_body).format_map(
            {
                **{
                    f"get_func_level_{i}": reindent(snip_get_func, level=i)
                    for i in range(2)
                },
                "get_func_with_args_level_2": reindent(
                    snip_get_func_with_args, level=2
                ),
            }
        )
        return ret

    def _snip_pre_check(self):
        return dedent(self._pre_check)

    def _snip_operator_sig(self):
        sig = "hier=None, "
        if self._extra_operator_sig or self._guessable:
            sig += "*, "
        if self._guessable:
            sig += "depth=None, "
        sig += self._extra_operator_sig
        return sig

    def _get_constants(self):
        objects = dict(
            create_hierarchy=create_hierarchy,
            guess_hierarchy=guess_hierarchy,
            value_arg_idx=self._value_arg_idx,
        )
        objects.update(self._get_extra_constants())
        objects.update(self._extra_constants)
        return objects

    def _get_extra_constants(self):
        return {}

    def compile(self) -> Callable:
        operator_sig = self._snip_operator_sig()
        constants = self._get_constants()

        snip_pre_check = self._snip_pre_check()
        snip_body = self._snip_body()

        func_body = "\n".join(
            [
                reindent(snip_pre_check, level=2, strip=False),
                reindent(snip_body, level=2, strip=False),
            ]
        )

        return make_func(self._name, operator_sig, func_body, constants)


class SimpleOperator(OperatorBase):
    def __post_init__(self, kwargs):
        self._build_func = None

    def build_func(self, f):
        self._build_func = f
        return f

    def _snip_get_func(self, call_args=""):
        snip = f"""
        return build_func(hier, {self._extra_operator_args}){call_args}
        """
        return dedent(snip)

    def _get_extra_constants(self):
        return dict(
            build_func=self._build_func,
        )


class VariadicOperator(OperatorBase):
    def __post_init__(self, kwargs):
        self._build_func_single_arg = None
        self._build_func_multi_arg = None
        self._extra_operator_sig += "ninputs=None, "

    def build_func_at_single_arg(self, f):
        self._build_func_single_arg = f
        return f

    def build_func_at_multi_arg(self, f):
        self._build_func_multi_arg = f
        return f

    def _snip_get_func(self, call_args=""):
        extra_args = self._extra_operator_args
        snip = f"""
        func_single_arg = build_func_single_arg(hier, {extra_args})
        func_multi_arg = build_func_multi_arg(hier, {extra_args})

        if ninputs is not None:
            if ninputs == 1:
                return func_single_arg{call_args}
            else:
                return func_multi_arg{call_args}

        def _func(*args):
            if len(args) > value_arg_idx + 1:
                return func_multi_arg(*args)
            else:
                return func_single_arg(*args)

        return _func{call_args}
        """
        return snip

    def _get_extra_constants(self):
        return dict(
            build_func_single_arg=self._build_func_single_arg,
            build_func_multi_arg=self._build_func_multi_arg,
        )
