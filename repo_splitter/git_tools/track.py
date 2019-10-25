from git import Repo


def track_all_remote_branches(repo: Repo):
    origin = repo.remote()
    for ref in origin.refs:
        branch_name = ref.remote_head
        if branch_name == 'HEAD':
            continue
        head = repo.create_head(branch_name, ref)
        repo.git.clear_cache()
        head.set_tracking_branch(ref)


def delete_non_active_local_branches(repo: Repo):
    for head in repo.heads:
        if head != repo.active_branch:
            repo.delete_head(head)
