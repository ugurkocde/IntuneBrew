#!/bin/bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
app="$stage/vendor.app"
mkdir -p "$app/Contents/MacOS"
cat > "$app/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?><plist version="1.0"><dict><key>CFBundleIdentifier</key><string>com.logi.optionsplus.installer</string><key>CFBundleVersion</key><string>2.8.981479</string><key>CFBundleExecutable</key><string>logioptionsplus_installer</string></dict></plist>
PLIST
cat > "$app/Contents/MacOS/logioptionsplus_installer" <<'SCRIPT'
#!/bin/bash
set -eu
test "$1" = --quiet
mkdir -p "$TEST_TARGET/Applications/logioptionsplus.app/Contents"
cat > "$TEST_TARGET/Applications/logioptionsplus.app/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?><plist version="1.0"><dict><key>CFBundleIdentifier</key><string>com.logi.optionsplus</string></dict></plist>
PLIST
SCRIPT
chmod 755 "$app/Contents/MacOS/logioptionsplus_installer"
bash "$root/.github/scripts/package_logi_options.sh" "$app" 2.8.981479 "$stage/logi.pkg"
pkgutil --expand-full "$stage/logi.pkg" "$stage/expanded"
test ! -d "$stage/expanded/Payload/Applications"
test -f "$stage/expanded/Scripts/postinstall"
TEST_TARGET="$stage/expanded/Payload" bash "$stage/expanded/Scripts/postinstall" "$stage/logi.pkg" / "$stage/expanded/Payload"
test -f "$stage/expanded/Payload/Applications/logioptionsplus.app/Contents/Info.plist"
printf '#!/bin/sh\nexit 42\n' > "$stage/expanded/Payload/usr/local/lib/intunebrew/logitech_options/logioptionsplus_installer.app/Contents/MacOS/logioptionsplus_installer"
if TEST_TARGET="$stage/expanded/Payload" bash "$stage/expanded/Scripts/postinstall" "$stage/logi.pkg" / "$stage/expanded/Payload"; then
  echo 'Vendor installation failure was incorrectly reported as success' >&2
  exit 1
fi
echo 'Logi Options+ package runs the installer and propagates failures'
