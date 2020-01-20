import os
import re
from typing import Set, Sequence

from git import Repo


def all_file_names_which_have_contained_the_lines_in_multiple_files(file_paths: Sequence[str], repo: Repo) -> Set[str]:
    """
    Parses the git log for all lines in multiple files, to determine all the file paths in which these lines
    have existed.

    Useful for tracking renames in a repo.

    :param file_paths: Relative paths to file within repo
    :param repo:
    :return:
    """
    all_names = set()
    for in_file in file_paths:
        all_names.update(
            all_file_names_which_have_contained_the_lines_in_a_file(in_file, repo)
        )
    return all_names


def all_file_names_which_have_contained_the_lines_in_a_file(file_path: str, repo: Repo) -> Set[str]:
    """
    Parses the git log for all lines in a file, to determine all the file paths in which these lines
    have existed.

    Useful for tracking renames in a repo.

    :param file_path: Relative path to file within repo
    :param repo:
    :return:
    """
    full_path = os.path.join(repo.working_tree_dir, file_path)

    if os.path.isdir(full_path):
        # Cannot detect changes directly on a directory
        return set()
    try:
        log = full_git_history_for_contents_of_file(full_path, repo)
    except EmptyFileException:
        return set()

    unique_matches = get_filenames_from_git_log(log)
    return unique_matches


def full_git_history_for_contents_of_file(file_path: str, repo: Repo) -> str:
    """
    Runs git log on all of the lines in a file
    """
    num_lines = file_length(file_path)
    if num_lines == 0:
        raise EmptyFileException('could not track history of lines in an empty file')
    file_search_str = f'1,{num_lines}:{file_path}'
    log = repo.git.log('--format=oneline', '--compact-summary', '-L', file_search_str)
    return log


def get_filenames_from_git_log(git_log: str) -> Set[str]:
    """

    :param git_log:
    :return:
    """
    pattern = re.compile(r'--- a\/(.+)\n\+\+\+ b\/(.+)')
    match_tuples = re.findall(pattern, git_log)
    unique_matches = {file for match_tup in match_tuples for file in match_tup}
    return unique_matches


def file_length(file_path: str) -> int:
    """
    Returns the number of lines in a file
    """
    i = -1
    with open(file_path) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


class EmptyFileException(Exception):
    pass