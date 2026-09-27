#!/usr/bin/env python3
"""Read-only audit of published PKGs. Never executes or modifies installers."""
import concurrent.futures
import hashlib
import json
import pathlib
import sys
import time

import requests


def inspect_package(name, manifest):
    result = {'app': name, 'version': manifest.get('version'), 'url': manifest['url'], 'expected': manifest.get('sha')}
    for attempt in range(3):
        try:
            digest = hashlib.sha256()
            size = 0
            prefix = b''
            with requests.get(manifest['url'], stream=True, timeout=(20, 120)) as response:
                response.raise_for_status()
                for chunk in response.iter_content(1024 * 1024):
                    prefix = (prefix + chunk)[:4]
                    digest.update(chunk)
                    size += len(chunk)
            result.update(actual=digest.hexdigest(), bytes=size, matches=digest.hexdigest() == manifest.get('sha'), validPkg=prefix == b'xar!' and size >= 28)
            return result
        except requests.RequestException as error:
            if attempt == 2:
                return {**result, 'error': str(error), 'matches': False, 'validPkg': False}
            time.sleep(2 ** attempt)


def main():
    manifests = [(path.stem, json.loads(path.read_text())) for path in pathlib.Path('Apps').glob('*.json')]
    packages = [(name, data) for name, data in manifests if not data.get('deprecated') and data.get('url', '').startswith('https://intunebrew.blob.core.windows.net/pkg/')]
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(inspect_package, name, data) for name, data in packages]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            if not result['matches'] or not result['validPkg']:
                print(f"::error::Package verification failed for {result['app']}", flush=True)
            if len(results) % 20 == 0:
                print(f'Checked {len(results)}/{len(packages)} packages', flush=True)
    pathlib.Path('package-checksum-audit.json').write_text(json.dumps(sorted(results, key=lambda result: result['app']), indent=2) + '\n')
    failures = sum(not result['matches'] or not result['validPkg'] for result in results)
    print(f'Checked {len(results)} packages; {failures} failures.')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
