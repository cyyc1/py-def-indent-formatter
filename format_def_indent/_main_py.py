# This file is inspired by https://github.com/asottile/add-trailing-comma/blob/6be6dfc05176bddfc5a9c4bf0fd4941850f0fb41/add_trailing_comma/_main.py  # noqa: E501

import argparse
import sys

from typing import Sequence, Optional

import format_def_indent._helper as helper
from format_def_indent._base_fixer import BaseFixer


class PythonFileFixer(BaseFixer):
    def __init__(self, path: str, cli_args: argparse.Namespace) -> None:
        super().__init__(path=path, cli_args=cli_args)

    def fix_one_file(self, filename: str) -> int:
        if filename == '-':
            source_bytes = sys.stdin.buffer.read()
        else:
            with open(filename, 'rb') as fb:
                source_bytes = fb.read()

        try:
            source_text_orig = source_text = source_bytes.decode()
        except UnicodeDecodeError:
            msg = f'{filename} is non-utf-8 (not supported)'
            print(msg, file=sys.stderr)
            return 1

        source_text = helper.fix_src(source_text)

        if filename == '-':
            print(source_text, end='')
        elif source_text != source_text_orig:
            print(f'Rewriting {filename}', file=sys.stderr)
            with open(filename, 'wb') as f:
                f.write(source_text.encode())

        if self.cli_args.exit_zero_even_if_changed:
            return 0
        else:
            return source_text != source_text_orig


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs='*')
    parser.add_argument('--exit-zero-even-if-changed', action='store_true')
    args = parser.parse_args(argv)

    ret = 0
    for path in args.paths:
        fixer = PythonFileFixer(path=path, cli_args=args)
        ret |= fixer.fix_one_directory_or_one_file()

    return ret


if __name__ == '__main__':
    raise SystemExit(main())
