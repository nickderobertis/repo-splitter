from typing import List

from git import Repo


def get_all_repo_files(repo: Repo, current_files_only: bool = False) -> List[str]:
    """
    Get all the file paths from a repo

    :param repo: git Repo
    :param current_files_only: if False, will search the entire git history for
        file names, defaults to False
    :return: File paths
    """
    if current_files_only:
        files = repo.git.ls_files().split('\n')
    else:
        files = _get_all_filenames_in_history_of_repo(repo)

    return files


def _get_all_filenames_in_history_of_repo(repo: Repo) -> List[str]:
    # git log will return all the files which
    # were ever added (A), renamed (R), or copied (C).
    files_str = repo.git.log('--pretty=format:', '--name-only', '--diff-filter=ARC')
    files_list = files_str.split('\n')
    files_set = set(files_list)
    if '' in files_set:
        files_set.remove('')
    files_list = list(files_set)
    files_list.sort()
    return files_list