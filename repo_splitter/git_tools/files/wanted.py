import os
from typing import Sequence, List
import glob

from git import Repo

from repo_splitter.git_tools.files.renames import all_file_names_which_have_contained_the_lines_in_multiple_files


def get_desired_files_from_patterns(repo: Repo, file_patterns: Sequence[str],
                                    follow_renames: bool = True) -> List[str]:
    """
    Pass glob file patterns relative to repo root such as data/** or code/* or code/my_module.py

    Handles resolving within the repo, and expanding globs into full relative file paths

    :param repo:
    :param file_patterns: A sequence of glob file patterns relative to repo root such as
    data/** or code/* or code/my_module.py
    :param follow_renames: Whether to track previous names of files from the history and also include those
    :return:
    """
    # TODO: needs to handle passing patterns which match old files not in the current working directory
    current_dir = os.getcwd()
    os.chdir(repo.working_tree_dir)
    all_files = []
    for file_pattern in file_patterns:
        all_files.extend(glob.glob(file_pattern, recursive=True))
    os.chdir(current_dir)

    if follow_renames:
        print(f'Following renames for {all_files}')
        all_files_set = set(all_files)
        new_files = all_file_names_which_have_contained_the_lines_in_multiple_files(all_files, repo)
        print(f'After tracking renames, added {new_files.difference(all_files_set)} to file list.')
        all_files_set.update(new_files)
        all_files = list(all_files_set)

    return all_files
