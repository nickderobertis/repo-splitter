from configparser import ConfigParser, SectionProxy
from typing import Any, Dict, Optional

from appdirs import AppDirs

APP_NAME = 'RepoSplitter'
GH_TOKEN_KEY = 'github_token'


def store_github_token(gh_token: str) -> None:
    """
    Stores the github token for later user

    :param gh_token: Github personal token
    :return:
    """
    set_config_item(GH_TOKEN_KEY, gh_token)


def get_github_token_from_config() -> Optional[str]:
    config = get_config_section()
    if not config or GH_TOKEN_KEY not in config:
        return
    return config[GH_TOKEN_KEY]


def remove_github_token_from_config() -> None:
    config = _load_config()
    if APP_NAME in config and GH_TOKEN_KEY in config[APP_NAME]:
        del config[APP_NAME][GH_TOKEN_KEY]
    _save_config(config)


def get_config_section() -> SectionProxy:
    config = _load_config()
    if APP_NAME not in config:
        config[APP_NAME] = {}
    return config[APP_NAME]


def set_config_item(item: str, value: Any) -> None:
    config = _load_config()
    if APP_NAME not in config:
        config[APP_NAME] = {}
    config[APP_NAME][item] = value
    _save_config(config)


def _load_config() -> ConfigParser:
    loc = _get_config_file_location()
    config = ConfigParser()
    config.read(loc)
    return config


def _save_config(conf: ConfigParser) -> None:
    loc = _get_config_file_location()
    print(f'Saving config to {loc}')
    with open(loc, 'w') as f:
        conf.write(f)


def _get_config_file_location() -> str:
    app_dirs = AppDirs(APP_NAME)
    return app_dirs.user_config_dir


