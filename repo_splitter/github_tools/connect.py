from git import Repo, Remote
from github.Repository import Repository


def connect_local_repo_to_github_repo(local_repo: Repo, github_repo: Repository) -> Remote:
    origin = local_repo.create_remote('origin', github_repo.clone_url)
    return origin
