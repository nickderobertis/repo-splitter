from git import Repo


def delete_remote(repo: Repo):
    origin = repo.remote()
    repo.delete_remote(origin)
