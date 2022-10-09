import argparse

from pathlib import Path


class BaseFixer:
    def __init__(self, path: str, cli_args: argparse.Namespace) -> None:
        self.path = path
        self.cli_args = cli_args

    def fix_one_directory_or_one_file(self) -> int:
        path_obj = Path(self.path)

        if path_obj.is_file():
            return self.fix_one_file(path_obj.as_posix())

        filenames = sorted(path_obj.rglob('*.py'))
        all_status = set()
        for filename in filenames:
            status = self.fix_one_file(filename)
            all_status.add(status)

        return 0 if all_status == {0} else 1

    def fix_one_file(self, *varargs, **kwargs):
        raise NotImplementedError('Please implement this method')
