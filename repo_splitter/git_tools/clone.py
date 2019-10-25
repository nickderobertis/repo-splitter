from git import Repo
from repo_splitter.git_tools.url import is_remote_url
from repo_splitter.git_tools.track import track_all_remote_branches, delete_non_active_local_branches


def clone_repo(source: str, dest: str, all_branches: bool = True, **kwargs):
    repo = _clone_repo(source, dest, **kwargs)

    if all_branches:
        track_all_remote_branches(repo)

    return repo


def _clone_repo(source, dest, **kwargs) -> Repo:
    return Repo.clone_from(source, dest, **kwargs)
