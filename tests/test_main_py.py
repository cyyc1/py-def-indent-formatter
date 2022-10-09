import argparse
import os
import shutil
import pytest

from typing import List, Tuple

from format_def_indent._main_py import PythonFileFixer


THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
RESOURCE_DIR = os.path.join(THIS_FILE_DIR, 'resources')


arg_parser = argparse.ArgumentParser(description='Argument parser')
arg_parser.add_argument('--exit-zero-even-if-changed', action='store_true')


test_cases = [
    ([], 1),
    (['--exit-zero-even-if-changed'], 0),
]


@pytest.mark.parametrize('cli_args, expected_return_value', test_cases)
def test_fix_python_file__fixed(cli_args, expected_return_value):
    filename_before, filename_after, filename_before_copy = _generate_filenames(
        case=1,
    )

    shutil.copyfile(filename_before, filename_before_copy)

    before_content = _read_file(filename_before_copy)
    after_content = _read_file(filename_after)

    assert before_content != after_content

    fixer = PythonFileFixer(
        path=filename_before_copy,
        cli_args=arg_parser.parse_args(cli_args),
    )
    ret_val = fixer.fix_one_directory_or_one_file()  # original file overwritten

    fixed_content = _read_file(filename_before_copy)  # re-read from hard drive
    os.remove(filename_before_copy)

    assert fixed_content == after_content
    assert ret_val == expected_return_value


def test_fix_python_file__nothing_to_fix():
    filename_before, filename_after, filename_before_copy = _generate_filenames(
        case=2,
    )

    shutil.copyfile(filename_before, filename_before_copy)

    before_content = _read_file(filename_before_copy)
    after_content = _read_file(filename_after)

    assert before_content == after_content  # because there's nothing to fix

    fixer = PythonFileFixer(
        path=filename_before_copy,
        cli_args=arg_parser.parse_args([]),
    )
    ret_val = fixer.fix_one_directory_or_one_file()  # original file overwritten

    fixed_content = _read_file(filename_before_copy)  # re-read from hard drive
    os.remove(filename_before_copy)

    # nothing is fixed
    assert fixed_content == after_content
    assert ret_val == 0


def _read_file(filename: str) -> List[str]:
    with open(filename) as fp:
        file_content = fp.readlines()

    return file_content


def _generate_filenames(case: int) -> Tuple[str, str, str]:
    filename_before = os.path.join(RESOURCE_DIR, f'case_{case}_before.py')
    filename_after = os.path.join(RESOURCE_DIR, f'case_{case}_after.py')
    filename_before_copy = os.path.join(RESOURCE_DIR, f'case_{case}_before-copy.py')
    return filename_before, filename_after, filename_before_copy
