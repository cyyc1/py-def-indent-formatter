import ast

from tokenize_rt import Offset
from tokenize_rt import src_to_tokens
from tokenize_rt import tokens_to_src


def fix_src(source_code: str) -> str:
    args_to_fix: set[Offset] = set()
    tree = ast.parse(source=source_code)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if len(node.args.args) > 0:
                args_base_lineno = node.args.args[0].lineno

                if args_base_lineno == node.lineno:
                    # All args are on the same line as "def function_name".
                    # There is no need to fix in this case.
                    pass
                else:
                    for i, arg_ in enumerate(node.args.args):
                        extra_offset = arg_.col_offset - node.col_offset
                        if extra_offset == 4:  # from `black` auto formatting
                            if i == 0 or (arg_.lineno != args_base_lineno):
                                line_col = Offset(arg_.lineno, arg_.col_offset)
                                args_to_fix.add(line_col)

    if not args_to_fix:
        return source_code

    tokens = src_to_tokens(source_code)

    for i, token in enumerate(tokens):
        if token.name == 'NAME' and token.offset in args_to_fix:
            old_src = token.src
            new_src = '    ' + old_src  # add 4 spaces
            tokens[i] = tokens[i]._replace(src=new_src)

    return tokens_to_src(tokens)
