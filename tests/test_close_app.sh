#!/bin/bash
set -eu
source "$(dirname "$0")/../scripts/close-app-before-install.sh"
app_is_running() { return 1; }
main
APP_BUNDLE_ID='invalid"identifier'
if main; then echo 'Invalid bundle identifier accepted' >&2; exit 1; fi
APP_BUNDLE_ID='com.example.fixture'
# Mock the external operations; no real applications are closed by this test.
console_uid() { echo 501; }
request_quit() { return 0; }
# Bypass the root check only inside this test process with a fixture executable.
# Remaining-app behavior is exercised on macOS CI under sudo.
if [[ "$(id -u)" == 0 ]]; then
    app_is_running() { return 0; }
    QUIT_TIMEOUT=1
    sleep() { :; }
    if main; then echo 'A running app incorrectly allowed installation' >&2; exit 1; fi
    request_quit() { app_is_running() { return 1; }; }
    main
fi
