#!/bin/bash
# Diagnostic only: never use this result to publish a package or bypass a check.
set -euo pipefail
test "${CI:-}" = true
test "${GITHUB_ACTIONS:-}" = true
test "${RUNNER_ENVIRONMENT:-}" = github-hosted
test "${RUNNER_OS:-}" = macOS
app=$1
requested=$2
archive=$3
test ! -e /Applications/logioptionsplus.app
codesign --verify --deep --strict -R '=anchor apple generic and certificate leaf[subject.OU] = "QED4VVPZWA"' "$app"
test "$(plutil -extract CFBundleIdentifier raw -o - "$app/Contents/Info.plist")" = com.logi.optionsplus.installer
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
feed='https://updates.optionsplus.logitechg.com/pipeline/v2/update/optionsplus5/osx/public/update.json'
curl --fail --silent --show-error --location --max-time 30 "$feed" > "$stage/before.json"
python - "$stage/before.json" "$requested" "$archive" "$app/Contents/Info.plist" <<'PY'
import hashlib, json, plistlib, re, sys
feed = json.load(open(sys.argv[1]))
assert re.fullmatch(r'\d+\.\d+\.\d+', sys.argv[2]), 'Unexpected requested version'
assert feed['version'] == sys.argv[2], 'Feed changed before diagnostic; no install'
with open(sys.argv[3], 'rb') as stream:
    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
with open(sys.argv[4], 'rb') as stream:
    bootstrap = plistlib.load(stream)['CFBundleVersion']
print(json.dumps({'diagnostic': 'logi-bootstrap-before', 'requestedVersion': sys.argv[2],
                  'feedVersion': feed['version'], 'bootstrapVersion': bootstrap, 'archiveSha256': digest,
                  'bootstrapExactTeamVerified': True}))
PY
# Run as root on this disposable runner only; suppress raw vendor logs and bound execution.
sudo "$(command -v python)" - "$app/Contents/MacOS/logioptionsplus_installer" "$stage/vendor.log" <<'PY'
import os, signal, subprocess, sys
with open(sys.argv[2], 'wb') as log:
    proc = subprocess.Popen([sys.argv[1], '--quiet'], stdout=log, stderr=subprocess.STDOUT,
                            start_new_session=True)
    try:
        code = proc.wait(timeout=240)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
        raise SystemExit('Logitech diagnostic exceeded 240 seconds')
    if code:
        raise SystemExit('Logitech diagnostic installer failed (raw log withheld)')
PY
installed=/Applications/logioptionsplus.app
codesign --verify --deep --strict -R '=anchor apple generic and certificate leaf[subject.OU] = "QED4VVPZWA"' "$installed"
curl --fail --silent --show-error --location --max-time 30 "$feed" > "$stage/after.json"
python - "$stage/after.json" "$requested" "$installed/Contents/Info.plist" <<'PY'
import json, plistlib, sys
feed = json.load(open(sys.argv[1]))
with open(sys.argv[3], 'rb') as stream:
    app = plistlib.load(stream)
print(json.dumps({'diagnostic': 'logi-bootstrap-after', 'requestedVersion': sys.argv[2],
                  'feedVersion': feed['version'], 'installedBundleVersion': app.get('CFBundleVersion'),
                  'installedShortVersion': app.get('CFBundleShortVersionString'),
                  'installedExactTeamVerified': True}))
assert app['CFBundleIdentifier'] == 'com.logi.optionsplus', 'Installed identity differs'
assert feed['version'] == sys.argv[2], 'Feed changed during diagnostic'
assert app['CFBundleVersion'] == sys.argv[2], 'Installed version differs from requested/feed'
PY
