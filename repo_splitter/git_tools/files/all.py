from typing import List

from git import Repo


def get_all_repo_files(repo: Repo) -> List[str]:
    files = repo.git.ls_files().split('\n')
    return files