from github import Github
from github.Repository import Repository


def github_repo_from_clone_url(clone_url: str, token: str) -> Repository:
    ghub = Github(token)
    user = ghub.get_user()
    repo_result = None
    for repo in user.get_repos():
        if repo.clone_url == clone_url:
            repo_result = repo
            break

    if repo_result is None:
        raise NoSuchGithubRepositoryException(f'could not find a Github repository for this user matching '
                                              f'the clone url {clone_url}')

    return repo_result


class NoSuchGithubRepositoryException(Exception):
    pass