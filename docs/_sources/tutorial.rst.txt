.. _tutorial:

Getting started with repo_splitter
**********************************

Install
=======

Install via::

    pip install repo_splitter


To get more modern styling of the GUI, you can add Qt. Note that
if you do not already have it installed, this will be a large
download::

    pip install repo_splitter[Qt]

Usage
=========

To use the GUI, simply type::

    repo-splitter

For an overview of the CLI commands, do::

    repo-splitter --help

Split Repo
------------

This is the main functionality of the package, to split a repo into two repos. For
details of how to use the CLI, run::

    repo-splitter split --help

A typical usage to create the new repo and remove history from the old repo
would be as follows::

    repo-splitter split \
        'https://github.com/myuser/my-repo.git' \
        my_out_dir new-repo-name \
        '["files/to/remove", "relative/paths/**/with/globs"]' \
        09fgdfg5540d65sa565565d45694


A typical usage to create the new repo, but leave the old repo history untouched,
would be as follows::

    repo-splitter split \
        'https://github.com/myuser/my-repo.git' \
        my_out_dir new-repo-name \
        '["files/to/remove", "relative/paths/**/with/globs"]' \
        09fgdfg5540d65sa565565d45694 \
        --noremove_files_from_old_repo


For details on usage from Python, see :py:func:`.split_repo`.

Remove History from Repo
--------------------------

This could be used in cases where you just want to remove some files from the full
history of a repo. Or it may be used after running the split command without
cleaning up the existing repo history. For details of how to use the CLI, run::

    repo-splitter rmhist --help

A typical usage would be as follows::

    repo-splitter rmhist \
        'https://github.com/myuser/my-repo.git' \
        '["files/to/remove", "relative/paths/**/with/globs"]' \
        09fgdfg5540d65sa565565d45694

For details on usage from Python, see :py:func:`.remove_from_repo_history`.


Restore from Backup
-----------------------

A backup is automatically created when removing existing repo history. Use the
restore command after either splitting the repo or removing history
to revert to the original history from the backup. For details of how to
use the CLI, run::

    repo-splitter restore --help

A typical usage would be as follows::

    repo-splitter restore \
        'https://github.com/myuser/my-repo.git' \
        my_out_dir \
        09fgdfg5540d65sa565565d45694

For details on usage from Python, see :py:func:`.restore_from_backup`.
