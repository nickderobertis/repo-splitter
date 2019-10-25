from typing import Sequence

from git import Repo

from repo_splitter.git_tools.files.wanted import get_desired_files_from_patterns


def remove_history_for_files_not_matching(repo: Repo, file_patterns: Sequence[str]):
    wanted_files = get_desired_files_from_patterns(repo, file_patterns)

    starts_with_wanted_files = ['^' + file for file in wanted_files]
    wanted_files_str = '|'.join(starts_with_wanted_files)
    index_filter_cmd = f'git ls-files | grep -vE "{wanted_files_str}" | xargs git rm -rf --cached --ignore-unmatch'

    repo.git.filter_branch('--prune-empty', '--index-filter', index_filter_cmd, '--', '--all')
