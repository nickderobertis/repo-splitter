from typing import Sequence
import re

from git import Repo, GitCommandError

from repo_splitter.git_tools.files.unwanted import get_unwanted_files_from_repo
from repo_splitter.git_tools.files.wanted import get_desired_files_from_patterns


START_COMMIT_PATTERN = r"Start of output for commit: [\d\w]+"


def remove_history_for_files_not_matching(repo: Repo, file_patterns: Sequence[str]):
    wanted_files = get_desired_files_from_patterns(repo, file_patterns)
    _remove_history_except_for_files(repo, wanted_files)


def remove_history_for_files_matching(repo: Repo, file_patterns: Sequence[str]):
    unmatched_files = get_unwanted_files_from_repo(repo, file_patterns)
    _remove_history_except_for_files(repo, unmatched_files)


def _remove_history_except_for_files(repo: Repo, files: Sequence[str]) -> str:
    starts_with_wanted_files = ['^' + file for file in files]
    wanted_files_str = '|'.join(starts_with_wanted_files)
    # Need to check if any files come back from ls-files not in wanted files. If empty, this means that the only
    # remaining files are the desired files, which means that nothing should be done.
    index_filter_cmd = f"""
    ALL_FILES=$(git ls-files | grep -vE "{wanted_files_str}");
    if [ -n "$ALL_FILES" ]; then 
        printf "$ALL_FILES" | xargs --delimiter="\\n" git rm -rf --cached --ignore-unmatch; 
    fi
    """.strip()

    return index_filter_branch(repo, index_filter_cmd)


def index_filter_branch(repo: Repo, index_filter_cmd: str) -> str:
    # Add debug info
    index_filter_cmd = f"""
    set -x;
    echo "\n\n\nStart of output for commit: $GIT_COMMIT";
    echo $(printenv);
    {index_filter_cmd};
    EXIT_CODE=$?;
    echo "End of output for commit: $GIT_COMMIT \n\n\n";
    (exit $EXIT_CODE);
    """
    return _filter_branch(repo, '--prune-empty', '--index-filter', index_filter_cmd, '--', '--all')


def _filter_branch(repo: Repo, *args, **kwargs):
    try:
        output = repo.git.filter_branch(*args, **kwargs)
        return output
    except GitCommandError as e:
        exc = GitFilterBranchException.from_git_command_error(e)
        raise exc from None


class GitFilterBranchException(Exception):

    def __init__(self, status: int, stdout: str, stderr: str, *args, **kwargs):
        self.status = status
        self.stdout = stdout
        self.stderr = stderr

    @classmethod
    def from_git_command_error(cls, git_error: GitCommandError):
        return cls(
            git_error.status,
            git_error.stdout,
            git_error.stderr,
        )

    @staticmethod
    def _extract_from_last_commit(output: str) -> str:
        last_commit_start = [match for match in re.finditer(START_COMMIT_PATTERN, output)][-1].start(0)
        return output[last_commit_start:]

    def __str__(self):
        try:
            stdout = GitFilterBranchException._extract_from_last_commit(self.stdout)
            stderr = GitFilterBranchException._extract_from_last_commit(self.stderr)
        except IndexError:
            stdout = self.stdout
            stderr = self.stderr

        message = f"""
        Stdout:
        {stdout}

        Stderr:
        {stderr}

        Note: Full stdout and stderr available in exception exc.stdout and exc.stderr
        """
        return message
