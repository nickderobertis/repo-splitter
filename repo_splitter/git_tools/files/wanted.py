import os
from typing import Sequence, List
import glob

from git import Repo


def get_desired_files_from_patterns(repo: Repo, file_patterns: Sequence[str]) -> List[str]:
    """
    Pass glob file patterns relative to repo root such as data/** or code/* or code/my_module.py

    Handles resolving within the repo, and expanding globs into full relative file paths

    :param repo:
    :param file_patterns: A sequence of glob file patterns relative to repo root such as
    data/** or code/* or code/my_module.py
    :return:
    """
    current_dir = os.getcwd()
    os.chdir(repo.working_tree_dir)
    all_files = []
    for file_pattern in file_patterns:
        all_files.extend(glob.glob(file_pattern, recursive=True))
    os.chdir(current_dir)
    return all_files