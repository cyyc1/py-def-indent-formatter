# The function structure of this file follows https://github.com/asottile/add-trailing-comma/blob/6be6dfc05176bddfc5a9c4bf0fd4941850f0fb41/add_trailing_comma/_main.py  # noqa: E501

import argparse
import sys

from pathlib import Path
from typing import Sequence

import format_def_indent._helper as helper


def fix_one_file(filename: str, args: argparse.Namespace) -> int:
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

    if args.exit_zero_even_if_changed:
        return 0
    else:
        return source_text != source_text_orig


def fix_one_directory(folder_name: str, args: argparse.Namespace) -> int:
    path_obj = Path(folder_name)

    if path_obj.is_file():
        return fix_one_file(path_obj.as_posix(), args=args)

    filenames = sorted(path_obj.rglob('*.py'))
    all_status = set()
    for filename in filenames:
        status = fix_one_file(filename, args=args)
        all_status.add(status)

    return 0 if all_status == {0} else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs='*')
    parser.add_argument('--exit-zero-even-if-changed', action='store_true')
    args = parser.parse_args(argv)

    ret = 0
    for path in args.paths:
        ret |= fix_one_directory(path, args)

    return ret


if __name__ == '__main__':
    raise SystemExit(main())
