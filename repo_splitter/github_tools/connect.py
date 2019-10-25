from git import Repo, Remote
from github.Repository import Repository
from github import Github


def connect_local_repo_to_github_repo(local_repo: Repo, github_repo: Repository, token: str) -> Remote:
    url = _github_authenticated_url(github_repo, token)
    origin = local_repo.create_remote('origin', url)
    return origin


def _github_authenticated_url(github_repo: Repository, token: str) -> str:
    username = _username_from_token(token)
    return github_repo.clone_url.replace('github.com', f'{username}:{token}@github.com')


def _username_from_token(token: str) -> str:
    ghub = Github(token)
    user = ghub.get_user()
    username = user.login
    return username