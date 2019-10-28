import shutil
import os
import tempfile
import time
from typing import Sequence, Optional

import fire
from git import Repo

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
               remove_files_from_old_repo: bool = True, keep_backup: bool = True,
               auto_push_remove: bool = False, backup_dir: Optional[str] = None):
    """
    Splits an existing Git repository into two repositories by selecting which files should be
    split into a new one.

    :param repo_source: clone url (remote) or file path (local) of repo that should be split
    :param repo_dest: folder in which the new repo should be placed
    :param new_repo_name: name for the new repo
    :param keep_files: files to be kept in the new repo
    :param github_token: personal access token for Github
    :param all_branches: whether to include all branches in the new repo or only the primary (remote)/active (local) one
    :param include_tags: whether to keep tags from the old repo in the new one
    :param remove_files_from_old_repo: whether to remove the split files and history from the original repo
    :param keep_backup: whether to retain a backup of the original repo in case something went wrong in removing history
    :param auto_push_remove: pass True to avoid prompt for whether to push the original repo with history removed
    :param backup_dir: pass file path to put backup of old repo there, otherwise uses repo_dest
    :return:
    """
    if keep_backup:
        backup_dir = _set_backup_dir(backup_dir, repo_dest)

    _split_repo(
        repo_source,
        repo_dest,
        new_repo_name,
        keep_files,
        github_token,
        all_branches=all_branches,
        include_tags=include_tags
    )

    if not remove_files_from_old_repo:
        print('Success')
        return

    remove_from_repo_history(
        repo_source,
        keep_files,
        github_token,
        keep_backup=keep_backup,
        auto_push_remove=auto_push_remove,
        backup_dir=backup_dir
    )




def _split_repo(repo_source: str, repo_dest: str, new_repo_name: str, keep_files: Sequence[str],
                github_token: str, all_branches: bool = False, include_tags: bool = False) -> Repo:
    with tempfile.TemporaryDirectory() as repo_temp_dest:
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

    full_repo_dest = os.path.join(repo_dest, new_repo_name)
    print(f'Cloning {new_repo_name} in permanent spot {full_repo_dest}. Will wait 5s for changes to become available.')
    time.sleep(5)
    os.makedirs(full_repo_dest)
    repo = clone_repo(github_repo.clone_url, full_repo_dest, all_branches=all_branches)
    return repo


def _set_backup_dir(backup_dir: str, repo_dest: str, require_empty: bool = True):
    if backup_dir is None:
        backup_dir = os.path.join(repo_dest, 'backup')
    if require_empty and os.path.exists(backup_dir) and os.listdir(backup_dir):
        raise ValueError(f'backup folder {backup_dir} already exists. Remove it or pass keep_backup=False')
    return backup_dir


def remove_from_repo_history(repo_source: str, drop_files: Sequence[str],
                             github_token: str, keep_backup: bool = True,
                             auto_push_remove: bool = False, backup_dir: Optional[str] = None):
    """
    Remove the passed files from the repo history entirely

    :param repo_source: clone url (remote) or file path (local) of repo that should be split
    :param drop_files: files to be dropped in the repo history
    :param github_token: personal access token for Github
    :param keep_backup: whether to retain a backup of the original repo in case something went wrong in removing history
    :param auto_push_remove: pass True to avoid prompt for whether to push the original repo with history removed
    :param backup_dir: pass file path to put backup of old repo there, otherwise uses repo_dest
    :return:
    """
    if keep_backup:
        backup_repo = clone_repo(repo_source, backup_dir, all_branches=True)

    print(f'Cleaning up what was split off in the old repo')
    with tempfile.TemporaryDirectory() as repo_temp_dest:
        print(f'Cloning {repo_source} into temporary directory')
        repo = clone_repo(repo_source, repo_temp_dest, all_branches=True)
        if is_remote_url(repo_source):
            # If remote, need to add authentication into the remote
            github_repo = github_repo_from_clone_url(repo_source, github_token)
            delete_remote(repo)
            connect_local_repo_to_github_repo(repo, github_repo, github_token)

        print(f'Removing history in the original repo for files which were split off')
        remove_history_for_files_matching(repo, drop_files)

        if not auto_push_remove:
            print('Success. Please inspect the old repo to make sure nothing that was needed was removed.')
            print('Once the history looks correct, enter Y to replace the remote repo contents')
            print('If there is an issue with the history, enter N to exit')
            push_repo_raw = input(f'Push modified history to {repo_source}? Y/N: ')
            push_repo_str = push_repo_raw.strip().lower()[0]
            push_repo = push_repo_str == 'y'
        else:
            print('auto_push_remove passed. Will automatically push to remote for original repo.')
            push_repo = True
        if push_repo:
            print('Pushing to remote for the original repo')
            push_all_force(repo)
            print('If there is an issue, '
                  'then you can go to your original local repo and run git push --all --force to reverse it')
        else:
            print('Not pushing modified history to original remote.')
        print('Removing temporary directory')


def restore_from_backup(repo_source: str, repo_dest: str, github_token: str, backup_dir: Optional[str] = None):
    """
    Restores a repo to original after running split_repo or remove_from_repo_history

    :param repo_source: clone url (remote) or file path (local) of repo that should be restored
    :param repo_dest: folder in which the local repo is placed
    :param github_token: personal access token for Github
    :param backup_dir: location of existing backup, default in folder backup inside repo_dest
    :return:
    """
    backup_dir = _set_backup_dir(backup_dir, repo_dest, require_empty=False)
    if not os.path.exists(backup_dir):
        raise ValueError(f'No backup found at {backup_dir}')

    repo = Repo(backup_dir)
    if is_remote_url(repo_source):
        # If remote, need to add authentication into the remote
        github_repo = github_repo_from_clone_url(repo_source, github_token)
        delete_remote(repo)
        connect_local_repo_to_github_repo(repo, github_repo, github_token)
        push_all_force(repo)

    shutil.rmtree(repo_dest)
    os.makedirs(repo_dest)
    shutil.copytree(backup_dir, repo_dest)


def main():
    return fire.Fire({
        'split': split_repo,
        'rmhist': remove_from_repo_history,
        'restore': restore_from_backup,
    })


if __name__ == '__main__':
    main()
