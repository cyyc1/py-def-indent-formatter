import argparse
import json
import sys
from typing import Sequence, Optional

from jupyter_notebook_parser import JupyterNotebookParser, JupyterNotebookRewriter

import format_def_indent._helper as helper
from format_def_indent._base_fixer import BaseFixer


class JupyterNotebookFixer(BaseFixer):
    def __init__(self, path: str, cli_args: argparse.Namespace) -> None:
        super().__init__(path=path, cli_args=cli_args)

    def fix_one_file(self, filename: str) -> int:
        try:
            parsed = JupyterNotebookParser(filename)
            rewriter = JupyterNotebookRewriter(parsed_notebook=parsed)
            code_cells = parsed.get_code_cells()
            code_cell_indices = parsed.get_code_cell_indices()
            code_cell_sources = parsed.get_code_cell_sources()
        except Exception as exc:
            print(f'Error reading {filename}: {str(exc)}', file=sys.stderr)
            return 1
        else:
            ret_val = 0
            assert len(code_cells) == len(code_cell_indices)
            assert len(code_cells) == len(code_cell_sources)

            for i in range(len(code_cells)):
                index: int = code_cell_indices[i]
                source: str = code_cell_sources[i]
                fixed: str = helper.fix_src(source_code=source)

                if fixed != source:
                    ret_val = 1
                    rewriter.replace_source_in_code_cell(
                        index=index,
                        new_source=fixed,
                    )

            if ret_val == 1:
                print(f'Rewriting {filename}', file=sys.stderr)
                with open(filename, 'w') as fp:
                    json.dump(parsed.notebook_content, fp, indent=1)
                    # Jupyter notebooks (.ipynb) always ends with a new line
                    # but json.dump does not.
                    fp.write('\n')

            return 0 if self.cli_args.exit_zero_even_if_changed else ret_val


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs='*')
    parser.add_argument('--exit-zero-even-if-changed', action='store_true')
    args = parser.parse_args(argv)

    ret = 0
    for path in args.paths:
        fixer = JupyterNotebookFixer(path=path, cli_args=args)
        ret |= fixer.fix_one_directory_or_one_file()

    return ret


if __name__ == '__main__':
    raise SystemExit(main())
