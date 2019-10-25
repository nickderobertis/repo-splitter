from github import Github


def create_repo(token: str, repo_name: str):
    ghub = Github(token)
    user = ghub.get_user()
    return user.create_repo(repo_name)