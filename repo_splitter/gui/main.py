from copy import deepcopy
from typing import Optional
from dataclasses import dataclass

import PySimpleGUI as sg


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


@dataclass
class SelectRepoConfig:
    new_repo_name: str
    gh_token: str

    repo_url: Optional[str] = None
    repo_local_path: Optional[str] = None

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



def repo_select_gui() -> Optional[SelectRepoConfig]:
    sg.theme(THEME)

    config: Optional[SelectRepoConfig] = None

    # All the stuff inside your window.
    layout = [  [sg.Text('Please select either a remote repo by URL or a local repo.')],
                [sg.Text('Repo by URL:'), sg.InputText(key='repo_loc_url')],
                [sg.Text('Local repo:'), sg.FolderBrowse(key='repo_loc_file_path')],
                [sg.Text('New Repo Name:'), sg.InputText(key='new_repo_name')],
                [sg.Text('Github Token:'), sg.InputText(key='gh_token')],
                [sg.Button('Ok'), sg.Button('Cancel')] ]

    # Create the Window
    window = sg.Window('Window Title', layout)
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
                )
                break
            except MustProvideRepoException:
                sg.Popup('Please provide either a repo URL or local repo path')
            except MustProvideInputException as e:
                sg.Popup(f'Please provide {e.input_name}')

    window.close()
    return config


def select_files_gui():
    sg.theme(THEME)

    orig_to_select = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
    orig_selected = []
    all_items = orig_to_select + orig_selected

    # All the stuff inside your window.
    layout = [  [sg.Text('Please select which files should be split from the repo.')],
                [
                    sg.Listbox(orig_to_select, **FILES_LISTBOX_SETTINGS, key='files_to_select'),
                    sg.Col([
                        [sg.Button('>')],
                        [sg.Button('<')],
                        [sg.Button('>>')],
                        [sg.Button('<<')],
                    ]),
                    sg.Listbox(orig_selected, **FILES_LISTBOX_SETTINGS, key='files_selected')
                ],
                [sg.Button('Ok'), sg.Button('Cancel')] ]

    # Create the Window
    window = sg.Window('Window Title', layout)
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
        if event == '>':
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
    config = repo_select_gui()
    if not config:
        return
    select_files_gui()

if __name__ == "__main__":
    repo_splitter_gui()