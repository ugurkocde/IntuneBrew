#!/usr/bin/env python3
"""Publish generated catalog changes without rebasing whole JSON documents."""
import json
import pathlib
import subprocess
import tempfile
import time
import sys

MISSING = object()
PATHS = ['Apps/*.json', 'supported_apps.json', 'README.md', 'catalog-sync.json', 'latest-updates.json']


def git(*args, cwd=None, check=True):
    return subprocess.run(['git', *args], cwd=cwd, check=check, capture_output=True)


def merge_json(base, generated, current, path=''):
    if generated == base:
        return current
    if current == base or generated == current:
        return generated
    if all(isinstance(value, dict) for value in (base, generated, current)):
        result = {}
        for key in sorted(base.keys() | generated.keys() | current.keys()):
            value = merge_json(base.get(key, MISSING), generated.get(key, MISSING), current.get(key, MISSING), f'{path}/{key}')
            if value is not MISSING:
                result[key] = value
        return result
    raise ValueError(f'Concurrent changes to the same catalog field: {path}. Run a fresh build.')


def content_at(ref, path):
    result = git('show', f'{ref}:{path}', check=False)
    return result.stdout if result.returncode == 0 else None


def merge_content(path, base, generated, current):
    if generated == base:
        return current
    if current == base or generated == current:
        return generated
    if path == '.github/pending-requests.json':
        def requests_by_issue(value):
            return {str(entry['issue']): entry for entry in json.loads(value or b'[]')}
        result = merge_json(requests_by_issue(base), requests_by_issue(generated), requests_by_issue(current), path)
        return (json.dumps(list(result.values()), indent=2) + '\n').encode()
    if path.endswith('.json'):
        decode = lambda value: json.loads(value) if value is not None else MISSING
        result = merge_json(decode(base), decode(generated), decode(current), path)
        if path.startswith('Apps/') and isinstance(result, dict):
            built = decode(generated)
            if isinstance(built, dict) and built.get('packageIdentifier') and result.get('bundleId') != built['packageIdentifier']:
                raise ValueError(f'Concurrent CLI package identifier change in {path}. Rebuild the package.')
        return None if result is MISSING else (json.dumps(result, indent=2, ensure_ascii=False) + '\n').encode()
    if None in (base, generated, current):
        raise ValueError(f'Concurrent addition/removal of {path}. Run a fresh build.')
    with tempfile.TemporaryDirectory() as directory:
        files = [pathlib.Path(directory) / name for name in ('generated', 'base', 'current')]
        for file, content in zip(files, (generated, base, current)):
            file.write_bytes(content)
        result = git('merge-file', '-p', *map(str, files), check=False)
        if result.returncode:
            raise ValueError(f'Concurrent changes to {path}. Run a fresh build.')
        return result.stdout


def main(pending=False, approval=False):
    selected_paths = (['.github/scripts/collect_app_info.py', '.github/pending-requests.json'] if approval
                      else ['.github/pending-requests.json'] if pending else PATHS)
    base_ref = git('rev-parse', 'HEAD').stdout.decode().strip()
    changed = git('diff', '--name-only', '-z', 'HEAD', '--', *selected_paths).stdout
    untracked = git('ls-files', '--others', '--exclude-standard', '-z', '--', *selected_paths).stdout
    paths = sorted(set(p.decode() for p in (changed + untracked).split(b'\0') if p))
    if not paths:
        print('No catalog changes to publish.')
        return
    snapshot = {path: (content_at(base_ref, path), pathlib.Path(path).read_bytes() if pathlib.Path(path).exists() else None) for path in paths}
    for attempt in range(5):
        git('fetch', 'origin', 'main')
        target = git('rev-parse', 'FETCH_HEAD').stdout.decode().strip()
        with tempfile.TemporaryDirectory(prefix='catalog-publish-') as directory:
            worktree = pathlib.Path(directory) / 'checkout'
            git('worktree', 'add', '--detach', str(worktree), target)
            try:
                for path, (base, generated) in snapshot.items():
                    merged = merge_content(path, base, generated, content_at(target, path))
                    destination = worktree / path
                    if merged is None:
                        destination.unlink(missing_ok=True)
                    else:
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        destination.write_bytes(merged)
                git('add', '--', *paths, cwd=worktree)
                if git('diff', '--staged', '--quiet', cwd=worktree, check=False).returncode == 0:
                    print('Catalog changes are already published.')
                    return
                message = ('Record approved app request' if approval else
                           'Acknowledge app request notifications [skip ci]' if pending else
                           'Update app information and supported apps list')
                git('commit', '-m', message, cwd=worktree)
                result = git('push', 'origin', 'HEAD:refs/heads/main', cwd=worktree, check=False)
                if result.returncode == 0:
                    print('Catalog snapshot published with concurrent metadata preserved.')
                    return
                # Do not print authenticated remote URLs from Git error output.
                print(f'Publication attempt {attempt + 1} failed; refreshing main before retry.')
            finally:
                git('worktree', 'remove', '--force', str(worktree))
        if attempt < 4:
            time.sleep(2 ** attempt)
    raise RuntimeError('Catalog publication failed after five attempts. Check repository write access and concurrent updates.')


if __name__ == '__main__':
    main(pending='--pending' in sys.argv, approval='--approval' in sys.argv)
