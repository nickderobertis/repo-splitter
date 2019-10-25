from typing import Sequence

from git import Repo

from repo_splitter.git_tools.files.unwanted import get_unwanted_files_from_repo
from repo_splitter.git_tools.files.wanted import get_desired_files_from_patterns


def remove_history_for_files_not_matching(repo: Repo, file_patterns: Sequence[str]):
    wanted_files = get_desired_files_from_patterns(repo, file_patterns)
    _remove_history_except_for_files(repo, wanted_files)


def remove_history_for_files_matching(repo: Repo, file_patterns: Sequence[str]):
    unmatched_files = get_unwanted_files_from_repo(repo, file_patterns)
    _remove_history_except_for_files(repo, unmatched_files)


def _remove_history_except_for_files(repo: Repo, files: Sequence[str]):
    starts_with_wanted_files = ['^' + file for file in files]
    wanted_files_str = '|'.join(starts_with_wanted_files)
    index_filter_cmd = f'git ls-files | grep -vE "{wanted_files_str}" | xargs git rm -rf --cached --ignore-unmatch'

    repo.git.filter_branch('--prune-empty', '--index-filter', index_filter_cmd, '--', '--all')
