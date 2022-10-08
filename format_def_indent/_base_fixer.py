import argparse

from pathlib import Path


class BaseFixer:
    def __init__(self, folder_name: str, cli_args: argparse.Namespace) -> None:
        self.folder_name = folder_name
        self.cli_args = cli_args

    def fix_one_directory(self) -> int:
        path_obj = Path(self.folder_name)

        if path_obj.is_file():
            return self.fix_one_file(path_obj.as_posix(), args=self.cli_args)

        filenames = sorted(path_obj.rglob('*.py'))
        all_status = set()
        for filename in filenames:
            status = self.fix_one_file(filename, args=self.cli_args)
            all_status.add(status)

        return 0 if all_status == {0} else 1

    def fix_one_file(self, *args, **kwargs):
        raise NotImplementedError('Please implement this method')
