from copy import deepcopy
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import tempfile
import os
import webbrowser


from git import Repo
from github.Repository import Repository

from repo_splitter.config import remove_github_token_from_config
from repo_splitter.gui.config import sg, THEME
from repo_splitter.git_tools.clone import clone_repo
from repo_splitter.git_tools.history import _remove_history_except_for_files
from repo_splitter.git_tools.push import push_all_force
from repo_splitter.git_tools.remote import delete_remote
from repo_splitter.git_tools.files.all import get_all_repo_files
from repo_splitter.git_tools.files.wanted import get_desired_files_from_patterns
from repo_splitter.gui.loading import loading_gui

FILES_LISTBOX_SETTINGS = dict(
    size=(50, 20),
    select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED
)


class MustProvideInputException(Exception):

    def __init__(self, *args, input_name: Optional[str] = None, **kwargs):
        self.input_name = input_name
        super().__init__(*args, **kwargs)


class MustProvideRepoException(MustProvideInputException):
    pass


class MustProvideOnlyOneRepoException(Exception):
    pass


class MustDoSomethingException(Exception):
    pass


@dataclass
class SelectRepoConfig:
    new_repo_name: str
    gh_token: str

    repo_url: Optional[str] = None
    repo_local_path: Optional[str] = None
    all_branches: Optional[bool] = False
    include_tags: Optional[bool] = False
    remove_files_from_old_repo: Optional[bool] = True
    create_new_repo: Optional[bool] = True
    store_gh_token: Optional[bool] = True

    def __post_init__(self):
        print(self)
        self._validate()

    def _validate(self):
        required_inputs = {
            'new_repo_name': 'New Repo Name',
            'gh_token': 'Github Token'
        }
        for inp_key, inp_name in required_inputs.items():
            if not getattr(self, inp_key):
                raise MustProvideInputException(input_name=inp_name)
        self._validate_repo()
        self._validate_options()

    def _validate_repo(self):
        if not self.repo_url and not self.repo_local_path:
            raise MustProvideRepoException
        if self.repo_url and self.repo_local_path:
            raise MustProvideOnlyOneRepoException

    def _validate_options(self):
        if not self.remove_files_from_old_repo and not self.create_new_repo:
            raise MustDoSomethingException


    @property
    def repo_loc(self) -> str:
        if self.repo_url:
            return self.repo_url
        if self.repo_local_path:
            return self.repo_local_path
        raise MustProvideRepoException


def repo_select_gui(defaults: Optional[Dict[str, Any]] = None) -> Optional[SelectRepoConfig]:
    expected_defaults = [
        'repo_loc_url',
        'new_repo_name',
        'github_token',
    ]
    if not defaults:
        defaults = {}
    for def_key in expected_defaults:
        if def_key not in defaults:
            defaults[def_key] = ''

    sg.theme(THEME)

    config: Optional[SelectRepoConfig] = None

    # All the stuff inside your window.
    layout = [  [sg.Text('Please select either a remote repo by URL or a local repo.')],
                [sg.Text('Repo by URL:'), sg.InputText(key='repo_loc_url', default_text=defaults['repo_loc_url'])],
                [sg.Text('Local repo:'), sg.FolderBrowse(key='repo_loc_file_path')],
                [sg.Text('New Repo Name:'), sg.InputText(key='new_repo_name', default_text=defaults['new_repo_name'])],
                [sg.Text('Github Token:'), sg.InputText(key='gh_token', default_text=defaults['github_token'])],
                [sg.Checkbox('Split all branches', key='all_branches')],
                [sg.Checkbox('Include tags in new repo', key='include_tags')],
                [sg.Checkbox('Create new repo from selected files', key='create_new_repo', default=True)],
                [sg.Checkbox('Remove history from the old repo', key='remove_files_from_old_repo', default=True)],
                [sg.Checkbox('Store Github Token for later use', key='store_gh_token', default=True)],
                [sg.Button('Ok'), sg.Button('Cancel')] ]

    # Create the Window
    window = sg.Window('Repo Splitter - Select Repo', layout)
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()
        if event in (None, 'Cancel'):   # if user closes window or clicks cancel
            break
        elif event == 'Ok':
            try:
                config = SelectRepoConfig(
                    values['new_repo_name'],
                    values['gh_token'],
                    repo_url=values['repo_loc_url'],
                    repo_local_path=values['repo_loc_file_path'],
                    all_branches=values['all_branches'],
                    include_tags=values['include_tags'],
                    remove_files_from_old_repo=values['remove_files_from_old_repo'],
                    create_new_repo=values['create_new_repo'],
                    store_gh_token=values['store_gh_token'],
                )
                break
            except MustProvideRepoException:
                sg.Popup('Please provide either a repo URL or local repo path')
            except MustProvideOnlyOneRepoException:
                sg.Popup('Please provide only one of repo URL and local repo path')
            except MustProvideInputException as e:
                sg.Popup(f'Please provide {e.input_name}')
            except MustDoSomethingException:
                sg.Popup(f'Must either create a new repo or remove history from old repo or both, '
                         f'or else what are you trying to do?')

    window.close()
    return config


def select_files_gui(files: List[str], repo: Repo) -> List[str]:
    sg.theme(THEME)

    orig_to_select = files
    orig_selected = []
    all_items = orig_to_select + orig_selected

    # All the stuff inside your window.
    layout = [  [sg.Text('Please select which files should be split from the repo.')],
                [
                    sg.Text('Enter a glob pattern:'),
                    sg.InputText(key='file_pattern'),
                    sg.Checkbox('Include renames', default=True, key='include_renames'),
                    sg.Button('Match'),
                ],
                [
                    sg.Col([
                        [sg.Text("Don't Split"), sg.Button('Sort', key='sort_left')],
                        [sg.Listbox(orig_to_select, **FILES_LISTBOX_SETTINGS, key='files_to_select')],
                    ]),
                    sg.Col([
                        [sg.Text('')],
                        [sg.Text('')],
                        [sg.Button('>')],
                        [sg.Button('<')],
                        [sg.Button('>>')],
                        [sg.Button('<<')],
                    ]),
                    sg.Col([
                        [sg.Text("Split"), sg.Button('Sort', key='sort_right')],
                        [sg.Listbox(orig_selected, **FILES_LISTBOX_SETTINGS, key='files_selected')],
                    ]),

                ],
                [sg.Button('Ok'), sg.Button('Cancel')] ]

    # Create the Window
    window = sg.Window('Repo Splitter - Select Files', layout)
    # Event Loop to process "events" and get the "values" of the inputs
    exit_on_close = True
    while True:
        event, values = window.read()
        if event in (None, 'Cancel'):   # if user closes window or clicks cancel
            break
        if event == 'Ok':
            exit_on_close = False
            break
        left_selected = deepcopy(values['files_to_select'])
        right_selected = deepcopy(values['files_selected'])
        left_listbox = window['files_to_select']
        right_listbox = window['files_selected']
        left_all_values = left_listbox.Values
        right_all_values = right_listbox.Values
        if event == 'Match':
            # Handle glob match to move files to right
            file_pattern = values['file_pattern']
            include_renames = values['include_renames']
            matched_files = get_desired_files_from_patterns(repo, [file_pattern], follow_renames=include_renames)
            for item in matched_files:
                if item in left_all_values:
                    left_all_values.remove(item)
                if item in all_items and item not in right_all_values:
                    right_all_values.append(item)
        elif event == 'sort_left':
            left_all_values.sort()
        elif event == 'sort_right':
            right_all_values.sort()
        elif event == '>':
            # Add left selected items to right listbox
            for item in left_selected:
                left_all_values.remove(item)
                right_all_values.append(item)
        elif event == '<':
            # Add right selected items to left listbox
            for item in right_selected:
                left_all_values.append(item)
                right_all_values.remove(item)
        elif event == '>>':
            # Add all left items to right listbox
            left_all_values = []
            right_all_values = all_items
        elif event == '<<':
            # Add all right items to left listbox
            left_all_values = all_items
            right_all_values = []

        left_listbox.update(left_all_values)
        right_listbox.update(right_all_values)
        print('values: ', values)
        print('event: ', event)
        print('left listbox', left_listbox.__dict__)
        print('right listbox', right_listbox.__dict__)

    right_listbox = window['files_selected']
    final_selected_values = right_listbox.Values

    window.close()

    if exit_on_close:
        exit(0)

    return final_selected_values


def dismiss_message_gui(message: str, title: Optional[str] = 'Notice'):
    sg.theme(THEME)

    # All the stuff inside your window.
    layout = [[sg.Text(message)],
              [sg.Button('Ok')]]

    # Create the Window
    window = sg.Window(title, layout)
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()
        if event in (None, 'Ok'):  # if user closes window or clicks cancel
            break

    window.close()


def should_push_old_repo_gui(temp_repo_dest: str) -> bool:
    sg.theme(THEME)

    message = f"""
The old repo has the history removed in a temporary repo in {temp_repo_dest}. Please examine 
the history in detail. If everything looks correct, click "Remove History" to remove the 
history from the old repo. This will overwrite the existing remote repo. If there is some issue
or you do not want to push the overwritten history, press "Cancel".
    """.strip()

    # All the stuff inside your window.
    layout = [[sg.Text(message)],
              [sg.Button('Remove History'), sg.Button('Cancel')]]

    # Create the Window
    window = sg.Window('Successfully Removed History From Old Repo. Push it?', layout)
    # Event Loop to process "events" and get the "values" of the inputs
    push_history = False
    while True:
        event, values = window.read()
        if event in (None, 'Cancel'):  # if user closes window or clicks cancel
            break
        if event == 'Remove History':
            push_history = True
            break

    window.close()

    return push_history


def show_created_repo_gui(gh_repo: Repository):
    sg.theme(THEME)

    # All the stuff inside your window.
    layout = [[sg.Text(f'The new repo {gh_repo.name} is now available. Click the following link to view:')],
              [sg.Text(gh_repo.url, click_submits=True, text_color='blue', key='url_clicked')],
              [sg.Button('Ok')]]

    # Create the Window
    window = sg.Window('Successfully Created New Repo', layout)
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()
        if event in (None, 'Ok'):  # if user closes window or clicks cancel
            break
        if event == 'url_clicked':
            webbrowser.open(gh_repo.url)


    window.close()


def repo_splitter_gui(**defaults):
    from repo_splitter.__main__ import (
        _create_github_repo_connect_local_repo,
        _set_backup_dir,
        _clone_and_connect
    )
    from repo_splitter.config import store_github_token

    ### TEMP, for testing
    defaults.update(dict(
        repo_loc_url='https://github.com/nickderobertis/dero.git',
        new_repo_name='testme',
    ))
    ### END TEMP

    config = repo_select_gui(defaults)

    if not config:
        return

    if config.store_gh_token:
        store_github_token(config.gh_token)
    else:
        remove_github_token_from_config()

    with tempfile.TemporaryDirectory(dir=os.path.expanduser('~')) as repo_temp_dest:
        def clone_and_delete_remote():
            repo = clone_repo(config.repo_loc, repo_temp_dest, all_branches=config.all_branches)
            delete_remote(repo)
            return repo

        repo = loading_gui(
            clone_and_delete_remote,
            'Cloning the repo. This may take a long time for larger repos.'
        )
        files = get_all_repo_files(repo)
        selected_files = select_files_gui(files, repo)

        if config.create_new_repo:
            loading_gui(
                _remove_history_except_for_files,
                'Removing history from the temporary repo. This will take a long time '
                'for large repos with many branches',
                repo,
                selected_files
            )

            github_repo = loading_gui(
                _create_github_repo_connect_local_repo,
                'Creating new Github repo',
                repo,
                config.new_repo_name,
                config.gh_token,
                all_branches=config.all_branches,
                include_tags=config.include_tags
            )

        if not config.remove_files_from_old_repo:
            show_created_repo_gui(github_repo)
            exit(0)

    with tempfile.TemporaryDirectory(dir=os.path.expanduser('~')) as repo_temp_dest:
        def make_backup_clone_old_repo():
            # TODO: better handling for backup location
            backup_dir = _set_backup_dir(None, os.getcwd())
            backup_repo = clone_repo(config.repo_loc, backup_dir, all_branches=True)
            repo = _clone_and_connect(config.repo_loc, repo_temp_dest, config.gh_token)
            return repo

        old_repo = loading_gui(
            make_backup_clone_old_repo,
            f'Cloning old repo into a temporary directory {repo_temp_dest}',
        )

        to_remove_from_old = [file for file in files if file not in selected_files]

        loading_gui(
            _remove_history_except_for_files,
            'Removing history from the temporary old repo. This will take a long time '
            'for large repos with many branches. Note that nothing will be pushed to the remote '
            'in this step.',
            old_repo,
            to_remove_from_old
        )

        should_push = should_push_old_repo_gui(repo_temp_dest)

        if should_push:
            push_all_force(old_repo)
            dismiss_message_gui(
                'Old repo pushed to remote. Please check it to make sure everything looks correct',
                title='Successfully Pushed Old Repo'
            )

        if config.create_new_repo:
            show_created_repo_gui(github_repo)



if __name__ == "__main__":
    repo_splitter_gui()