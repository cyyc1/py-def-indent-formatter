import ast
from typing import Set, List

from tokenize_rt import Token
from tokenize_rt import Offset
from tokenize_rt import src_to_tokens
from tokenize_rt import tokens_to_src

FOUR_SPACES = '    '


def fix_src(source_code: str) -> str:
    args_to_fix: set[Offset] = set()
    tree = ast.parse(source=source_code)
    _collect_args_to_fix(tree, args_to_fix=args_to_fix)

    if not args_to_fix:
        return source_code

    tokens = src_to_tokens(source_code)
    _fix_tokens(tokens, args_to_fix=args_to_fix)

    return tokens_to_src(tokens)


def _collect_args_to_fix(tree: ast.Module, args_to_fix: Set[Offset]) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
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

            if all_args:
                min_arg_lineno = min(_.lineno for _ in all_args)
            else:
                min_arg_lineno = None

            if min_arg_lineno is not None and min_arg_lineno != node.lineno:
                if regular_args:
                    for i, arg_ in enumerate(regular_args):
                        _collect_if_not_correctly_indented(
                            arg_=arg_,
                            parent_node=node,
                            min_lineno_of_all_args=min_arg_lineno,
                            forbidden_offset=4,
                            is_0th_arg=arg_.lineno == min_arg_lineno,
                            collection=args_to_fix,
                        )

                if node.args.vararg is not None:
                    _collect_if_not_correctly_indented(
                        arg_=node.args.vararg,
                        parent_node=node,
                        min_lineno_of_all_args=min_arg_lineno,
                        forbidden_offset=5,
                        is_0th_arg=node.args.vararg.lineno == min_arg_lineno,
                        collection=args_to_fix,
                    )

                if node.args.kwarg is not None:
                    _collect_if_not_correctly_indented(
                        arg_=node.args.kwarg,
                        parent_node=node,
                        min_lineno_of_all_args=min_arg_lineno,
                        forbidden_offset=6,
                        is_0th_arg=node.args.kwarg.lineno == min_arg_lineno,
                        collection=args_to_fix,
                    )


def _collect_if_not_correctly_indented(
        arg_: ast.arg,
        parent_node,
        min_lineno_of_all_args: int,
        forbidden_offset: int,
        is_0th_arg: bool,
        collection: set[Offset],
) -> None:
    if arg_.lineno == parent_node.lineno:
        # We don't need to fix args that are on the same line as as the
        # function definition. This is because we assume the input always
        # come from `black`'s output, so if it an arg is on the same line
        # as the function defition, it means the whole function signature
        # fits into one line, and there's nothing to fix.
        return

    extra_offset = arg_.col_offset - parent_node.col_offset
    if extra_offset == forbidden_offset:
        if is_0th_arg or arg_.lineno != min_lineno_of_all_args:
            collection.add(Offset(arg_.lineno, arg_.col_offset))


def _fix_tokens(tokens: List[Token], args_to_fix: Set[Offset]) -> None:
    for i, token in enumerate(tokens):
        if token.name == 'NAME' and token.offset in args_to_fix:
            if i > 0:
                prev_token = tokens[i - 1]
                if prev_token.name == 'OP' and prev_token.src in {'**', '*'}:
                    tokens[i - 1] = tokens[i - 1]._replace(
                        src=f'{FOUR_SPACES}{prev_token.src}',
                    )
                else:
                    tokens[i] = tokens[i]._replace(src=FOUR_SPACES + token.src)
            else:
                tokens[i] = tokens[i]._replace(src=FOUR_SPACES + token.src)
