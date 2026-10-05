"""Restore unbuilt catalog entries without overlapping Git readers and writers."""
import json
import os
from pathlib import Path
import subprocess


def git_paths(*args):
    result = subprocess.run(['git', '--no-optional-locks', *args], check=True, capture_output=True)
    return [os.fsdecode(path) for path in result.stdout.split(b'\0') if path]


def revert(tokens):
    # Materialize both path lists before any checkout. Process substitutions
    # can leave git diff refreshing/locking the index while checkout starts.
    tracked = git_paths('diff', '--name-only', '-z', '--', 'Apps/*.json')
    untracked = git_paths('ls-files', '--others', '--exclude-standard', '-z', '--', 'Apps/*.json')
    reverted = 0
    for paths, existing in [(tracked, True), (untracked, False)]:
        for filename in paths:
            try:
                cask = json.loads(Path(filename).read_text()).get('homebrew_cask')
            except (OSError, ValueError):
                cask = None
            if cask not in tokens:
                if existing:
                    subprocess.run(['git', 'restore', '--', filename], check=True)
                else:
                    Path(filename).unlink()
                reverted += 1
    subprocess.run(['git', 'restore', '--', 'README.md'], check=True)
    print(f'Reverted {reverted} out-of-scope app files')


if __name__ == '__main__':
    revert(set(os.environ['SCOPE_TOKENS'].split()))
