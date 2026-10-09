#!/usr/bin/env python3
"""Associate a cached PKG with its own checksum, never its vendor archive's."""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import time

import requests


def update_cached_package(manifest, previous, package_url, session=requests, sleep=time.sleep):
    filename = package_url.rsplit('/', 1)[-1]
    if not package_url.startswith('https://intunebrew.blob.core.windows.net/pkg/') or not filename.endswith('.pkg'):
        raise ValueError('Expected an IntuneBrew package URL.')
    for attempt in range(1, 4):
        try:
            return _verify_cached_package(manifest, previous, package_url, filename, session)
        except requests.exceptions.SSLError:
            # Certificate and hostname failures must never be retried.
            raise
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout,
                requests.exceptions.ChunkedEncodingError) as error:
            if attempt == 3:
                raise
            print(f'Transient error verifying {filename} (attempt {attempt}/3): {type(error).__name__}')
            sleep(attempt)


def _verify_cached_package(manifest, previous, package_url, filename, session):
    # Only a checksum already published for this exact package is reusable.
    checksum = previous.get('sha', '')
    trusted = (previous.get('url') == package_url and previous.get('fileName') == filename
               and previous.get('version') == manifest.get('version')
               and isinstance(checksum, str) and re.fullmatch(r'[a-fA-F0-9]{64}', checksum))
    if trusted:
        with session.get(package_url, headers={"Range": "bytes=0-27"}, stream=True, timeout=(20, 120)) as response:
            response.raise_for_status()
            prefix = b""
            for chunk in response.iter_content(28):
                prefix += chunk
                if len(prefix) >= 28:
                    break
            if len(prefix) < 28 or not prefix.startswith(b"xar!"):
                raise ValueError("Cached artifact is not a PKG archive.")
    else:
        digest = hashlib.sha256()
        first = True
        size = 0
        with session.get(package_url, stream=True, timeout=(20, 120)) as response:
            response.raise_for_status()
            for chunk in response.iter_content(1024 * 1024):
                if not chunk:
                    continue
                if first and not chunk.startswith(b'xar!'):
                    raise ValueError('Cached artifact is not a PKG archive.')
                first = False
                digest.update(chunk)
                size += len(chunk)
        if size < 28:
            raise ValueError('Cached package is empty or truncated.')
        checksum = digest.hexdigest()
    result = dict(manifest)
    result.update(url=package_url, fileName=filename, sha=checksum.lower())
    if not result.get('vendor_url') and manifest.get('url') != package_url:
        result['vendor_url'] = manifest.get('url')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('manifest', type=pathlib.Path)
    parser.add_argument('package_url')
    args = parser.parse_args()
    path = args.manifest.resolve()
    repository = path.parent.parent
    previous_result = subprocess.run(['git', '-C', str(repository), 'show', f'HEAD:Apps/{path.name}'], capture_output=True)
    previous = json.loads(previous_result.stdout) if previous_result.returncode == 0 else {}
    current = json.loads(path.read_text())
    updated = update_cached_package(current, previous, args.package_url)
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(updated, indent=2) + '\n')
    temporary.replace(path)
    print(f'Cached package checksum verified for {path.stem}.')


if __name__ == '__main__':
    main()
