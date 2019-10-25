from git import Repo


def push_active_branch(repo: Repo) -> str:
    return _push_branch(repo, repo.active_branch.name)


def push_all_branches(repo: Repo) -> str:
    output_lines = []
    for branch in repo.heads:
        output = _push_branch(repo, branch.name)
        output_lines.append(output)
    return '\n'.join(output_lines)


def push_tags(repo: Repo) -> str:
    return repo.git.push('origin', '--tags')


def push_all_force(repo: Repo) -> str:
    return repo.git.push('origin', '--all', '--force')


def _push_branch(repo: Repo, branch_name: str) -> str:
    return repo.git.push('-u', 'origin', branch_name)