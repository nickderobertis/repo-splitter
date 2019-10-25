import shutil
import os
import time
from typing import Sequence

from repo_splitter.git_tools.clone import clone_repo
from repo_splitter.git_tools.remote import delete_remote
from repo_splitter.git_tools.history import remove_history_for_files_not_matching, remove_history_for_files_matching
from repo_splitter.git_tools.url import is_remote_url
from repo_splitter.github_tools.create import create_repo
from repo_splitter.github_tools.connect import connect_local_repo_to_github_repo
from repo_splitter.git_tools.push import push_active_branch, push_all_branches, push_tags, push_all_force
from repo_splitter.github_tools.query import github_repo_from_clone_url


def split_repo(repo_source: str, repo_dest: str, new_repo_name: str, keep_files: Sequence[str],
               github_token: str, all_branches: bool = False, include_tags: bool = False,
               remove_files_from_old_repo: bool = True):
    repo_temp_dest = 'testrepo'  # TODO: tempdir

    print(f'Creating temporary repo from {repo_source}')
    repo = clone_repo(repo_source, repo_temp_dest, all_branches=all_branches)
    delete_remote(repo)

    print('Removing unwanted history from temporary repo')
    remove_history_for_files_not_matching(repo, keep_files)

    print(f'Creating Github repo {new_repo_name}')
    github_repo = create_repo(github_token, new_repo_name)

    print(f'Pushing local temporary repo to github repo {new_repo_name}')
    connect_local_repo_to_github_repo(repo, github_repo, github_token)
    if all_branches:
        push_all_branches(repo)
    else:
        push_active_branch(repo)

    if include_tags:
        push_tags(repo)

    print('Removing temporary directory')
    shutil.rmtree(repo_temp_dest)

    full_repo_dest = os.path.join(repo_dest, new_repo_name)
    print(f'Cloning {new_repo_name} in permanent spot {full_repo_dest}. Will wait 15s for changes to become available.')
    time.sleep(15)
    os.makedirs(full_repo_dest)
    repo = clone_repo(github_repo.clone_url, full_repo_dest, all_branches=all_branches)

    if not remove_files_from_old_repo:
        print('Success')
        return

    print(f'Cleaning up what was split off in the old repo')
    os.makedirs(repo_temp_dest)
    print(f'Cloning {repo_source} into temporary directory')
    repo = clone_repo(repo_source, repo_temp_dest, all_branches=True)
    if is_remote_url(repo_source):
        # If remote, need to add authentication into the remote
        github_repo = github_repo_from_clone_url(repo_source, github_token)
        delete_remote(repo)
        connect_local_repo_to_github_repo(repo, github_repo, github_token)

    print(f'Removing history in the original repo for files which were split off')
    remove_history_for_files_matching(repo, keep_files)

    print('Pushing to remote for the original repo')
    push_all_force(repo)

    print('Removing temporary directory')
    shutil.rmtree(repo_temp_dest)

    print('Success')



