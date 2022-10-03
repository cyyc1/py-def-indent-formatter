from timeit import repeat
import pytest
from format_def_indent._helper import fix_src


before_0a = ''  # trivial case (empty file)
after_0a = ''


before_0b = 'a = 2'  # nothing to fix
after_0b = before_0b


before_1 = """
def parent_func(
    x, y, z,
):
    def some_func(
        arg1,
        arg2,  # comments should be retained
        arg3: int,
        arg4: bool = True,
    ) -> int:
        print(1)
        print(2)
        pass

    print(2)
    return 2
"""

after_1 = """
def parent_func(
        x, y, z,
):
    def some_func(
            arg1,
            arg2,  # comments should be retained
            arg3: int,
            arg4: bool = True,
    ) -> int:
        print(1)
        print(2)
        pass

    print(2)
    return 2
"""


before_2a = """
def func2(arg1, arg2, arg3, arg4, arg5):
    return 2
"""

after_2a = before_2a


before_2b = """
def func2(arg1, arg2, arg3, arg4, arg5) -> int:
    def func3(
        arg_one,
        arg_two,
        arg_three,
    ):
        print(1)
    return 2
"""

after_2b = """
def func2(arg1, arg2, arg3, arg4, arg5) -> int:
    def func3(
            arg_one,
            arg_two,
            arg_three,
    ):
        print(1)
    return 2
"""


before_2c = """
def func1(arg1, arg2, arg3):
    pass

def func2(arg_one, arg_two, arg_three):
    pass

def func3(
    arg_1,
    arg_2,
    arg_3,
):
    pass

def func4(
    argA, argB, argC, argD,
):
    pass
"""

after_2c = """
def func1(arg1, arg2, arg3):
    pass

def func2(arg_one, arg_two, arg_three):
    pass

def func3(
        arg_1,
        arg_2,
        arg_3,
):
    pass

def func4(
        argA, argB, argC, argD,
):
    pass
"""


before_3 = """
def func3(
    arg1, arg_2, very_long_arg_3, also_very_long_arg4,  # some comments
):
    return 1
"""

after_3 = """
def func3(
        arg1, arg_2, very_long_arg_3, also_very_long_arg4,  # some comments
):
    return 1
"""


before_4a = """
class MyClass:
    def __init__(
        self,
        data,
    ):
        self.data = data

    def some_func(
        arg1, arg2, arg3, arg4,
    ):
        print(2)

    @classmethod
    def some_method(
        cls, arg1: int, arg2: dict,
    ) -> float:
        return 2.0
"""

after_4a = """
class MyClass:
    def __init__(
            self,
            data,
    ):
        self.data = data

    def some_func(
            arg1, arg2, arg3, arg4,
    ):
        print(2)

    @classmethod
    def some_method(
            cls, arg1: int, arg2: dict,
    ) -> float:
        return 2.0
"""


before_5a = """
def func0(
    argA,
    argB,
    *argC,
    **argD,
):
    pass
"""

after_5a = """
def func0(
        argA,
        argB,
        *argC,
        **argD,
):
    pass
"""


before_5b = """
def func0(arg1, *arg2, **arg3):
    pass
"""
after_5b = before_5b


before_5c = """
def func0(
    arg1, arg2, *arg3, **arg4,
):
    pass
"""

after_5c = """
def func0(
        arg1, arg2, *arg3, **arg4,
):
    pass
"""


before_999a = """
something = some_func(
    arg1, arg2=4, arg3=True,
)
"""

after_999a = before_999a  # because this is a function call, not a function def


before_999b = """
some_dict = {
    'a': 1,
    'b': 2,
}
"""

after_999b = before_999b  # again, this is not a function def, so nothing to fix


before_999c = """
def some_func(
      arg1,
      arg2,
      arg3,
):
    pass
"""
after_999c = before_999c  # indent ≠ 4 spaces; won't fix even if it's bad style


before_999d = """
def some_func(
 arg1,
  arg2,
   arg3,
):
    pass
"""
after_999d = before_999d  # indentation ≠ 4 spaces, so we don't fix this case


before_999e = """
def some_func(
   arg1,
    arg2,  # this is 4 spaces
     arg3,
):
    pass
"""

# Arguably it becomes worse style, but we assume users run "black" or "blue"
# formatter before running this formatter, so this case should not happen
# in reality:
after_999e = """
def some_func(
   arg1,
        arg2,  # this is 4 spaces
     arg3,
):
    pass
"""


test_cases = [
    (before_0a, after_0a),
    (before_0b, after_0b),
    (before_1, after_1),
    (before_2a, after_2a),
    (before_2b, after_2b),
    (before_2c, after_2c),
    (before_3, after_3),
    (before_4a, after_4a),
    (before_5a, after_5a),
    (before_5b, after_5b),
    (before_5c, after_5c),
    (before_999a, after_999a),
    (before_999b, after_999b),
    (before_999c, after_999c),
    (before_999d, after_999d),
    (before_999e, after_999e),
]


@pytest.mark.parametrize('before_src, after_src', test_cases)
def test_fix_src(before_src, after_src):
    assert fix_src(before_src) == after_src


@pytest.mark.parametrize('before_src, after_src', test_cases)
def test_fix_src__repeated_run(before_src, after_src):
    # This test makes sure the formatted code file stays the same no matter
    # how many times we format it.

    how_many_repeated_runs = 100  # this should be enough
    before_src_ = before_src
    for _ in range(how_many_repeated_runs):
        buffer = fix_src(before_src_)
        assert buffer == after_src
        before_src_ = buffer
