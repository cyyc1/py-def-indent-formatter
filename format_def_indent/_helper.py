import ast
from typing import Set, List, Tuple, Dict

from tokenize_rt import Token
from tokenize_rt import Offset
from tokenize_rt import src_to_tokens
from tokenize_rt import tokens_to_src

FOUR_SPACES = '    '


def fix_src(source_code: str) -> str:
    args_to_fix: Dict[Offset, ast.FunctionDef] = {}
    functions_with_one_line_kwonly_args: Set[ast.FunctionDef] = set()

    tree = ast.parse(source=source_code)
    _collect_args_to_fix(tree, args_to_fix, functions_with_one_line_kwonly_args)

    if not args_to_fix and not functions_with_one_line_kwonly_args:
        return source_code

    tokens = src_to_tokens(source_code)
    _fix_tokens(tokens, args_to_fix, functions_with_one_line_kwonly_args)

    return tokens_to_src(tokens)


def _collect_args_to_fix(
        tree: ast.Module,
        args_to_fix: Dict[Offset, ast.FunctionDef],
        functions_with_one_line_kwonly_args: Set[ast.FunctionDef],
) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            all_args, regular_args, all_args_kwonly = _collect_args_from_node(node)
            min_arg_lineno = _calc_min_arg_lineno(all_args=all_args)

            if all_args_kwonly:
                all_args_on_same_line = (
                    len({_.lineno for _ in node.args.kwonlyargs}) == 1
                )
                if all_args_on_same_line:
                    functions_with_one_line_kwonly_args.add(node)

            if min_arg_lineno is not None and min_arg_lineno != node.lineno:
                if regular_args:
                    for i, arg_ in enumerate(regular_args):
                        _collect_if_not_correctly_indented(
                            arg_=arg_,
                            parent_node=node,
                            min_lineno_of_all_args=min_arg_lineno,
                            forbidden_offset=4,
                            is_0th_arg=arg_.lineno == min_arg_lineno,
                            args_to_fix=args_to_fix,
                        )

                if node.args.vararg is not None:
                    _collect_if_not_correctly_indented(
                        arg_=node.args.vararg,
                        parent_node=node,
                        min_lineno_of_all_args=min_arg_lineno,
                        forbidden_offset=5,  # because the arg starts with '*'
                        is_0th_arg=node.args.vararg.lineno == min_arg_lineno,
                        args_to_fix=args_to_fix,
                    )

                if node.args.kwarg is not None:
                    _collect_if_not_correctly_indented(
                        arg_=node.args.kwarg,
                        parent_node=node,
                        min_lineno_of_all_args=min_arg_lineno,
                        forbidden_offset=6,  # because the arg starts with '**'
                        is_0th_arg=node.args.kwarg.lineno == min_arg_lineno,
                        args_to_fix=args_to_fix,
                    )


def _collect_args_from_node(node: ast.FunctionDef) -> Tuple[List, List, bool]:
    all_args = []
    regular_args = []

    regular_args.extend(node.args.args)
    regular_args.extend(node.args.posonlyargs)
    regular_args.extend(node.args.kwonlyargs)

    all_args.extend(regular_args)

    if node.args.vararg is not None:
        all_args.append(node.args.vararg)

    if node.args.kwarg is not None:
        all_args.append(node.args.kwarg)

    all_args_kwonly = (len(all_args) == len(node.args.kwonlyargs))

    return all_args, regular_args, all_args_kwonly


def _calc_min_arg_lineno(all_args: List[ast.arg]):
    if all_args:
        return min(_.lineno for _ in all_args)

    return None


def _collect_if_not_correctly_indented(
        arg_: ast.arg,
        parent_node,
        min_lineno_of_all_args: int,
        forbidden_offset: int,
        is_0th_arg: bool,
        args_to_fix: Dict[Offset, ast.FunctionDef],
) -> None:
    if arg_.lineno == parent_node.lineno:
        # We don't need to fix args that are on the same line as the
        # function definition. This is because we assume the input always
        # come from `black`'s output, so if all its args are on the same line
        # as the function definition, it means the whole function signature
        # fits into one line, and there's nothing to fix.
        return

    extra_offset = arg_.col_offset - parent_node.col_offset
    if extra_offset == forbidden_offset:
        if is_0th_arg or arg_.lineno != min_lineno_of_all_args:
            args_to_fix[Offset(arg_.lineno, arg_.col_offset)] = parent_node


def _fix_tokens(
        all_tokens: List[Token],
        args_to_fix: Dict[Offset, ast.FunctionDef],
        functions_with_one_line_kwonly_args: Set[ast.FunctionDef],
) -> None:
    for func in functions_with_one_line_kwonly_args:
        _fix_star_as_first_arg_and_all_args_on_same_line(
            all_tokens=all_tokens,
            arg_lineno=func.args.kwonlyargs[0].lineno,
            parent_function=func,
        )

    for i, token in enumerate(all_tokens):
        if token.name == 'NAME' and token.offset in args_to_fix:
            parent_node = args_to_fix[token.offset]

            _fix_star_in_args_other_cases(
                parent_node=parent_node,
                all_tokens=all_tokens,
                current_lineno=token.line,
            )

            if i > 0:
                prev_token = all_tokens[i - 1]
                if prev_token.name == 'OP' and prev_token.src in {'**', '*'}:
                    all_tokens[i - 1] = all_tokens[i - 1]._replace(
                        src=f'{FOUR_SPACES}{prev_token.src}',
                    )
                else:
                    all_tokens[i] = all_tokens[i]._replace(src=FOUR_SPACES + token.src)
            else:
                all_tokens[i] = all_tokens[i]._replace(src=FOUR_SPACES + token.src)


def _fix_star_as_first_arg_and_all_args_on_same_line(
        all_tokens: List[Token],
        arg_lineno: int,
        parent_function: ast.FunctionDef,
) -> None:
    """
    Fix the following kind of function definitions, where all arguments are on
    the same line, '*,' precedes all arguments:

    >>> def some_func(*, arg1, arg2, arg3):
    >>>     print(1)
    """
    for i, token in enumerate(all_tokens):
        if (
                token.line == arg_lineno
                and token.name == 'OP'
                and token.src == '*'
                and token.utf8_byte_offset - parent_function.col_offset == 4
        ):
            all_tokens[i] = all_tokens[i]._replace(src=FOUR_SPACES + '*')


def _fix_star_in_args_other_cases(
        parent_node: ast.FunctionDef,
        all_tokens: List[Token],
        current_lineno: int,
) -> None:
    """
    Fix '*,' in the argument list, except for the case mentioned in
    _fix_star_as_first_arg_and_all_args_on_same_line()

    We need to specially treat '*,' because '*,' does not appear anywhere
    in the parsed AST structure.
    """

    # We only care about '*,' that appears within the range of a function
    token_indices_in_func = _collect_tokens_within_function_def_range(
        start_lineno=parent_node.lineno,
        end_lineno=parent_node.end_lineno,
        all_tokens=all_tokens,
    )
    for j in token_indices_in_func[1:-1]:
        # We start from 1 and end at -1, because '*' cannot be the 0th token
        # or the last token of a valid piece of Python function definition.
        this_token = all_tokens[j]
        prev_token = all_tokens[j - 1]
        next_token = all_tokens[j + 1]
        if (
                this_token.name == 'OP'
                and this_token.src == '*'
                and prev_token.name != 'NAME'

                # Since we assume the input code are already formatted by
                # "black", we can assume no spaces between '*' and ','
                and next_token.name == 'OP' and next_token.src == ','

                # If '*,' and the current argument are on the same line, it
                # means that '*,' is in between different arguments (Because
                # we have already dealt with the case where '*,' is the 0th
                # argument.)
                # Therefore, no need to fix this_token.line == current_lineno
                and this_token.line != current_lineno
        ):
            all_tokens[j] = all_tokens[j]._replace(src=FOUR_SPACES + '*')


def _collect_tokens_within_function_def_range(
        *,
        start_lineno: int,
        end_lineno: int,
        all_tokens: List[Token],
) -> List[int]:
    qualifying_token_indices = []
    for i, token in enumerate(all_tokens):
        if start_lineno <= token.line <= end_lineno:
            qualifying_token_indices.append(i)

    return qualifying_token_indices
