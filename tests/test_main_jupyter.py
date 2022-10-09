import argparse
import os
import shutil
import pytest

from typing import Tuple

from jupyter_notebook_parser import JupyterNotebookParser

from format_def_indent._main_jupyter import JupyterNotebookFixer


THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
RESOURCE_DIR = os.path.join(THIS_FILE_DIR, 'resources')


arg_parser = argparse.ArgumentParser(description='Argument parser')
arg_parser.add_argument('--exit-zero-even-if-changed', action='store_true')


test_cases = [
    ([], 1),
    (['--exit-zero-even-if-changed'], 0),
]


@pytest.mark.parametrize('cli_args, expected_return_value', test_cases)
def test_fix_jupyter_notebook__fixed(cli_args, expected_return_value):
    filename_before, filename_after, filename_before_copy = _generate_filenames(
        case=1,
    )

    shutil.copyfile(filename_before, filename_before_copy)

    parsed_before = JupyterNotebookParser(filename_before_copy)
    parsed_after = JupyterNotebookParser(filename_after)

    assert parsed_before.notebook_content != parsed_after.notebook_content

    fixer = JupyterNotebookFixer(
        path=filename_before_copy,
        cli_args=arg_parser.parse_args(cli_args),
    )
    ret_val = fixer.fix_one_directory_or_one_file()  # original file overwritten

    fixed = JupyterNotebookParser(filename_before_copy)  # re-read from disk
    os.remove(filename_before_copy)

    assert fixed.notebook_content == parsed_after.notebook_content
    assert ret_val == expected_return_value


def test_fix_jupyter_notebook__nothing_to_fix():
    filename_before, filename_after, filename_before_copy = _generate_filenames(
        case=2,
    )

    shutil.copyfile(filename_before, filename_before_copy)

    parsed_before = JupyterNotebookParser(filename_before_copy)
    parsed_after = JupyterNotebookParser(filename_after)

    # there's nothing to fix
    assert parsed_before.notebook_content == parsed_after.notebook_content

    fixer = JupyterNotebookFixer(
        path=filename_before_copy,
        cli_args=arg_parser.parse_args([]),
    )
    ret_val = fixer.fix_one_directory_or_one_file()  # original file overwritten

    fixed = JupyterNotebookParser(filename_before_copy)  # re-read from disk
    os.remove(filename_before_copy)

    # nothing is fixed
    assert fixed.notebook_content == parsed_after.notebook_content
    assert ret_val == 0


@pytest.mark.parametrize('cli_args, expected_return_value', test_cases)
def test_fix_jupyter_notebook__ipython_magics(cli_args, expected_return_value):
    filename_before, filename_after, filename_before_copy = _generate_filenames(
        case=3,
    )

    shutil.copyfile(filename_before, filename_before_copy)

    parsed_before = JupyterNotebookParser(filename_before_copy)
    parsed_after = JupyterNotebookParser(filename_after)

    assert parsed_before.notebook_content != parsed_after.notebook_content

    fixer = JupyterNotebookFixer(
        path=filename_before_copy,
        cli_args=arg_parser.parse_args(cli_args),
    )
    ret_val = fixer.fix_one_directory_or_one_file()  # original file overwritten

    fixed = JupyterNotebookParser(filename_before_copy)  # re-read from disk
    os.remove(filename_before_copy)

    assert fixed.notebook_content == parsed_after.notebook_content
    assert ret_val == expected_return_value


def _generate_filenames(case: int) -> Tuple[str, str, str]:
    filename_before = os.path.join(RESOURCE_DIR, f'case_{case}_before.ipynb')
    filename_after = os.path.join(RESOURCE_DIR, f'case_{case}_after.ipynb')
    filename_before_copy = os.path.join(RESOURCE_DIR, f'case_{case}_before-copy.ipynb')
    return filename_before, filename_after, filename_before_copy
