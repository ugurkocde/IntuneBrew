#!/usr/bin/env python3
"""Associate a cached PKG with its own checksum, never its vendor archive's."""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import time
import sys
from urllib.parse import urlsplit

import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'lib'))
from font_payload import FONT_RECIPE


def font_cache_eligible(manifest, previous, app_key):
    """Not eligible means rebuild; malformed input or corrupt content means hold."""
    payload = manifest.get('font_payload')
    if (not re.fullmatch(r'[a-z0-9_]{1,64}', app_key) or manifest.get('type') != 'app'
            or not isinstance(manifest.get('version'), str)
            or not re.fullmatch(r'[0-9A-Za-z][0-9A-Za-z.+-]{0,63}', manifest['version'])
            or manifest.get('bundleId') != 'com.intunebrew.' + app_key
            or not isinstance(payload, dict) or set(payload) != {'source_url', 'archive_sha256', 'files'}):
        raise ValueError('Invalid font cache manifest')
    url = urlsplit(payload['source_url']) if isinstance(payload['source_url'], str) else None
    files = payload['files']
    if (url is None or url.scheme != 'https' or not url.hostname or url.username is not None
            or url.password is not None or url.fragment
            or not url.path.lower().endswith(('.zip', '.tar.xz', '.tar.gz', '.tgz', '.tar.bz2', '.tbz'))
            or any(c.isspace() or ord(c) < 32 for c in payload['source_url'])
            or not isinstance(payload['archive_sha256'], str)
            or not re.fullmatch(r'[0-9a-f]{64}', payload['archive_sha256'])
            or not isinstance(files, list) or not 1 <= len(files) <= 256):
        raise ValueError('Invalid font cache archive binding')
    for path in files:
        if (not isinstance(path, str) or not 1 <= len(path.split('/')) <= 8
                or not all(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 ._+-]{0,127}', p) for p in path.split('/'))
                or not path.lower().endswith(('.ttf', '.otf'))):
            raise ValueError('Invalid font cache file path')
    if len({path.rsplit('/', 1)[-1].casefold() for path in files}) != len(files):
        raise ValueError('Ambiguous font cache basenames')
    checksum = previous.get('sha', '')
    if not isinstance(checksum, str) or not re.fullmatch(r'[0-9a-f]{64}', checksum):
        return False
    filename = app_key + '_' + manifest['version'] + '.pkg'
    expected = 'https://intunebrew.blob.core.windows.net/pkg/fonts/' + app_key + '/' + checksum + '/' + filename
    return (previous.get('font_payload') == payload and previous.get('version') == manifest['version']
            and previous.get('type') == 'app' and previous.get('packaging_recipe') == FONT_RECIPE
            and previous.get('bundleId') == previous.get('packageIdentifier') == manifest['bundleId']
            and isinstance(checksum, str) and re.fullmatch(r'[0-9a-f]{64}', checksum) is not None
            and previous.get('url') == expected and previous.get('fileName') == filename)


def reuse_font_package(manifest, previous, app_key, session=requests):
    if not font_cache_eligible(manifest, previous, app_key):
        return None
    digest = hashlib.sha256(); size = 0; prefix = b''
    with session.get(previous['url'], stream=True, timeout=(20, 120)) as response:
        response.raise_for_status()
        for chunk in response.iter_content(1024 * 1024):
            if not chunk: continue
            size += len(chunk)
            if size > 2 * 1024 ** 3: raise ValueError('Cached font package exceeds size bound')
            prefix = (prefix + chunk)[:4]; digest.update(chunk)
    if size < 28 or prefix != b'xar!' or digest.hexdigest() != previous['sha']:
        raise ValueError('Cached font package hash or archive mismatch')
    result = dict(manifest)
    for key in ['url', 'fileName', 'sha', 'packaging_recipe', 'bundleId', 'packageIdentifier']:
        result[key] = previous[key]
    result['vendor_url'] = manifest['font_payload']['source_url']
    return result


def update_cached_package(manifest, previous, package_url, session=requests, sleep=time.sleep):
    if 'font_payload' in manifest or 'font_payload' in previous:
        raise ValueError('Font manifests require the exact font cache path')
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
    parser.add_argument('package_url', nargs='?')
    parser.add_argument('--font', action='store_true')
    args = parser.parse_args()
    path = args.manifest.resolve()
    repository = path.parent.parent
    previous_result = subprocess.run(['git', '-C', str(repository), 'show', f'HEAD:Apps/{path.name}'], capture_output=True)
    previous = json.loads(previous_result.stdout) if previous_result.returncode == 0 else {}
    current = json.loads(path.read_text())
    if args.font:
        if args.package_url is not None: parser.error('Font mode has no package URL argument')
        updated = reuse_font_package(current, previous, path.stem)
        if updated is None:
            return 10
    else:
        if args.package_url is None: parser.error('Package URL is required')
        updated = update_cached_package(current, previous, args.package_url)
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(updated, indent=2) + '\n')
    temporary.replace(path)
    print(f'Cached package checksum verified for {path.stem}.')


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        print('Cached package verification failed; catalog entry held.', file=sys.stderr)
        raise SystemExit(1)
