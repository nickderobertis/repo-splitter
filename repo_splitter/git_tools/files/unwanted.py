from typing import Sequence

from git import Repo

from repo_splitter.git_tools.files.all import get_all_repo_files
from repo_splitter.git_tools.files.wanted import get_desired_files_from_patterns


def get_unwanted_files_from_repo(repo: Repo, file_patterns: Sequence[str]):
    all_files = get_all_repo_files(repo)
    wanted_files = get_desired_files_from_patterns(repo, file_patterns)

    return [file for file in all_files if file not in wanted_files]
