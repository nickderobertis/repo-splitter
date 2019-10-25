from git import Repo, Remote
from github.Repository import Repository


def connect_local_repo_to_github_repo(local_repo: Repo, github_repo: Repository, username: str,
                                      token: str) -> Remote:
    url = _github_authenticated_url(github_repo, username, token)
    origin = local_repo.create_remote('origin', url)
    return origin


def _github_authenticated_url(github_repo: Repository, username: str, token: str) -> str:
    return github_repo.clone_url.replace('github.com', f'{username}:{token}@github.com')