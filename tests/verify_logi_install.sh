#!/bin/bash
# Exercise the built PKG only on credential-free disposable PR test runners.
set -euo pipefail
test "${CI:-}" = true
test "${GITHUB_ACTIONS:-}" = true
test "${RUNNER_ENVIRONMENT:-}" = github-hosted
test "${RUNNER_OS:-}" = macOS
pkg=$1
requested=$2
archive=$3
test -f "$pkg"
test ! -e /Applications/logioptionsplus.app
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
feed='https://updates.optionsplus.logitechg.com/pipeline/v2/update/optionsplus5/osx/public/update.json'
curl --fail --silent --show-error --location --max-time 30 "$feed" > "$stage/before.json"
python - "$stage/before.json" "$requested" "$archive" "$pkg" <<'PY'
import hashlib, json, re, sys
feed = json.load(open(sys.argv[1]))
assert re.fullmatch(r'\d+\.\d+\.\d+', sys.argv[2]), 'Unexpected requested version'
assert feed['version'] == sys.argv[2], 'Feed changed before verification; no install'
def digest(path):
    value = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()
print(json.dumps({'verification': 'logi-pkg-before', 'requestedVersion': sys.argv[2],
                  'feedVersion': feed['version'], 'archiveSha256': digest(sys.argv[3]),
                  'packageSha256': digest(sys.argv[4])}))
PY
# Root can terminate the full installer process group; never print raw vendor logs.
sudo "$(command -v python)" - "$pkg" "$stage/vendor.log" <<'PY'
import os, signal, subprocess, sys
with open(sys.argv[2], 'wb') as log:
    proc = subprocess.Popen(['/usr/sbin/installer', '-pkg', sys.argv[1], '-target', '/'],
                            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        code = proc.wait(timeout=240)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()
        raise SystemExit('Logitech PKG verification exceeded 240 seconds')
    if code:
        raise SystemExit('Logitech PKG installation failed (raw log withheld)')
PY
installed=/Applications/logioptionsplus.app
codesign --verify --deep --strict -R '=anchor apple generic and certificate leaf[subject.OU] = "QED4VVPZWA"' "$installed"
curl --fail --silent --show-error --location --max-time 30 "$feed" > "$stage/after.json"
python - "$stage/after.json" "$requested" "$installed/Contents/Info.plist" <<'PY'
import json, plistlib, sys
feed = json.load(open(sys.argv[1]))
with open(sys.argv[3], 'rb') as stream:
    app = plistlib.load(stream)
print(json.dumps({'verification': 'logi-pkg-after', 'requestedVersion': sys.argv[2],
                  'feedVersion': feed['version'], 'installedBundleVersion': app.get('CFBundleVersion'),
                  'installedShortVersion': app.get('CFBundleShortVersionString'),
                  'installedExactTeamVerified': True}))
assert app['CFBundleIdentifier'] == 'com.logi.optionsplus', 'Installed identity differs'
assert feed['version'] == sys.argv[2], 'Feed changed during verification'
assert app['CFBundleVersion'] == sys.argv[2], 'Installed build version differs from requested/feed'
assert app['CFBundleShortVersionString'] == sys.argv[2], 'Installed short version differs from requested/feed'
PY
