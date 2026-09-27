#!/bin/bash
# Intune PKG pre-install example. Customize these values for the target app.
APP_BUNDLE_ID="${APP_BUNDLE_ID:-com.microsoft.Outlook}"
PROCESS_NAME="${PROCESS_NAME:-Microsoft Outlook}"
QUIT_TIMEOUT="${QUIT_TIMEOUT:-30}"

literal_process_pattern() { printf '%s' "$PROCESS_NAME" | /usr/bin/sed 's/[][\\.^$*+?(){}|]/\\&/g'; }
app_is_running() {
    local status=0
    /usr/bin/pgrep -x "$(literal_process_pattern)" >/dev/null 2>&1 || status=$?
    # Only a definite no-match (1) allows installation; lookup errors defer it.
    [[ "$status" != 1 ]]
}
console_uid() { /usr/bin/stat -f %u /dev/console; }
request_quit() {
    /bin/launchctl asuser "$1" /usr/bin/sudo -u "#$1" /usr/bin/osascript <<APPLESCRIPT
with timeout of $QUIT_TIMEOUT seconds
    if application id "$APP_BUNDLE_ID" is running then
        tell application id "$APP_BUNDLE_ID" to quit
    end if
end timeout
APPLESCRIPT
}

main() {
    if [[ ! "$APP_BUNDLE_ID" =~ ^[A-Za-z0-9]+([.-][A-Za-z0-9]+)+$ ]] ||
       [[ ! "$QUIT_TIMEOUT" =~ ^[0-9]+$ ]] || (( QUIT_TIMEOUT < 1 || QUIT_TIMEOUT > 120 )) ||
       [[ -z "$PROCESS_NAME" || "$PROCESS_NAME" == -* ]]; then
        echo 'Invalid app identifier, process name, or timeout.' >&2
        return 2
    fi
    if ! app_is_running; then
        echo 'The target app is already closed.'
        return 0
    fi
    if [[ "$(/usr/bin/id -u)" != 0 ]]; then
        echo 'Run this pre-install script as root.' >&2
        return 1
    fi
    local uid
    uid=$(console_uid) || return 1
    if [[ ! "$uid" =~ ^[0-9]+$ ]] || (( uid < 500 )); then
        echo 'The app is running without an eligible console user. Deferring installation.' >&2
        return 1
    fi
    # Unsaved work or automation denial may prevent quitting. Never force-kill.
    request_quit "$uid" || true
    local waited=0
    while app_is_running && (( waited < QUIT_TIMEOUT )); do
        sleep 1
        waited=$((waited + 1))
    done
    if app_is_running; then
        echo 'The app remains open. Ask the user to save and quit, then retry installation.' >&2
        return 1
    fi
    echo 'The app closed successfully.'
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    main "$@"
fi
