from copy import deepcopy
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import tempfile
import os

import PySimpleGUI as sg
from git import Repo

from repo_splitter.git_tools.clone import clone_repo
from repo_splitter.git_tools.remote import delete_remote
from repo_splitter.git_tools.files.all import get_all_repo_files
from repo_splitter.git_tools.files.wanted import get_desired_files_from_patterns


FILES_LISTBOX_SETTINGS = dict(
    size=(50, 20),
    select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED
)

THEME = 'DarkAmber'


class MustProvideInputException(Exception):

    def __init__(self, *args, input_name: Optional[str] = None, **kwargs):
        self.input_name = input_name
        super().__init__(*args, **kwargs)


class MustProvideRepoException(MustProvideInputException):
    pass


class MustProvideOnlyOneRepoException(Exception):
    pass


@dataclass
class SelectRepoConfig:
    new_repo_name: str
    gh_token: str

    repo_url: Optional[str] = None
    repo_local_path: Optional[str] = None
    all_branches: Optional[bool] = False

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

    def _validate_repo(self):
        if not self.repo_url and not self.repo_local_path:
            raise MustProvideRepoException
        if self.repo_url and self.repo_local_path:
            raise MustProvideOnlyOneRepoException

    @property
    def repo(self) -> str:
        if self.repo_url:
            return self.repo_url
        if self.repo_local_path:
            return self.repo_local_path
        raise MustProvideRepoException



def repo_select_gui(defaults: Optional[Dict[str, Any]] = None) -> Optional[SelectRepoConfig]:
    if not defaults:
        defaults = dict(
            repo_loc_url='',
            new_repo_name='',
            gh_token=''
        )

    sg.theme(THEME)

    config: Optional[SelectRepoConfig] = None

    # All the stuff inside your window.
    layout = [  [sg.Text('Please select either a remote repo by URL or a local repo.')],
                [sg.Text('Repo by URL:'), sg.InputText(key='repo_loc_url', default_text=defaults['repo_loc_url'])],
                [sg.Text('Local repo:'), sg.FolderBrowse(key='repo_loc_file_path')],
                [sg.Text('New Repo Name:'), sg.InputText(key='new_repo_name', default_text=defaults['new_repo_name'])],
                [sg.Text('Github Token:'), sg.InputText(key='gh_token', default_text=defaults['gh_token'])],
                [sg.Checkbox('Split all branches:', key='all_branches')],
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
                    all_branches=values['all_branches']
                )
                break
            except MustProvideRepoException:
                sg.Popup('Please provide either a repo URL or local repo path')
            except MustProvideOnlyOneRepoException:
                sg.Popup('Please provide only one of repo URL and local repo path')
            except MustProvideInputException as e:
                sg.Popup(f'Please provide {e.input_name}')

    window.close()
    return config


def select_files_gui(files: List[str], repo: Repo):
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
    while True:
        event, values = window.read()
        if event in (None, 'Cancel'):   # if user closes window or clicks cancel
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

    window.close()


def repo_splitter_gui():

    ### TEMP, for testing
    defaults = dict(
        repo_loc_url='https://github.com/nickderobertis/dero.git',
        new_repo_name='testme',
        gh_token=''
    )
    config = repo_select_gui(defaults)
    ### END TEMP
    ### TEMP COMMENTED
    # config = repo_select_gui()
    #### END TEMP COMMENTED


    if not config:
        return
    with tempfile.TemporaryDirectory(dir=os.path.expanduser('~')) as repo_temp_dest:
        repo = clone_repo(config.repo, repo_temp_dest, all_branches=config.all_branches)
        delete_remote(repo)
        files = get_all_repo_files(repo)
        select_files_gui(files, repo)

if __name__ == "__main__":
    repo_splitter_gui()