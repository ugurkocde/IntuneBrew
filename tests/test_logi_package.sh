#!/bin/bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
mkdir "$stage/tools"
cat > "$stage/tools/codesign" <<'SCRIPT'
#!/bin/bash
set -eu
test "$1" = --verify
test "$5" = '=anchor apple generic and certificate leaf[subject.OU] = "QED4VVPZWA"'
exit "${TEST_SIGNATURE_STATUS:-0}"
SCRIPT
chmod 755 "$stage/tools/codesign"
cat > "$stage/tools/curl" <<'SCRIPT'
#!/bin/bash
set -eu
case "${TEST_FEED_MODE:-match}" in
  error) exit 22 ;;
  malformed) echo '{broken'; exit 0 ;;
  missing) echo '{}'; exit 0 ;;
  mismatch) echo '{"version":"2.8.981479"}'; exit 0 ;;
  drift)
    if [ -f "$TEST_CURL_STATE" ]; then echo '{"version":"2.10.1"}'; else
      touch "$TEST_CURL_STATE"
      echo '{"version":"2.9.994631"}'
    fi
    exit 0 ;;
esac
echo '{"version":"2.9.994631"}'
SCRIPT
chmod 755 "$stage/tools/curl"
export PATH="$stage/tools:$PATH"
export TEST_CURL_STATE="$stage/curl-state"
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
bash "$root/.github/scripts/package_logi_options.sh" "$app" 2.9.994631 "$stage/logi.pkg"
pkgutil --expand-full "$stage/logi.pkg" "$stage/expanded"
python - "$stage/expanded/PackageInfo" <<'PY'
import sys, xml.etree.ElementTree as ET
assert ET.parse(sys.argv[1]).getroot().attrib['version'] == '2.9.994631'
PY
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
if TEST_SIGNATURE_STATUS=1 bash "$root/.github/scripts/package_logi_options.sh" "$app" 2.9.994631 "$stage/untrusted.pkg"; then
  echo 'Untrusted vendor signature was accepted' >&2
  exit 1
fi
test ! -f "$stage/untrusted.pkg"
for mode in mismatch drift error malformed missing; do
  rm -f "$TEST_CURL_STATE"
  if TEST_FEED_MODE="$mode" bash "$root/.github/scripts/package_logi_options.sh" "$app" 2.9.994631 "$stage/$mode.pkg"; then
    echo "Invalid or changing feed accepted: $mode" >&2
    exit 1
  fi
  test ! -f "$stage/$mode.pkg"
done
if bash "$root/.github/scripts/package_logi_options.sh" "$app" 'not-a-version' "$stage/invalid.pkg"; then
  echo 'Malformed requested version accepted' >&2
  exit 1
fi
test ! -f "$stage/invalid.pkg"
/usr/bin/plutil -replace CFBundleIdentifier -string com.example.wrong "$app/Contents/Info.plist"
if bash "$root/.github/scripts/package_logi_options.sh" "$app" 2.9.994631 "$stage/wrong-id.pkg"; then
  echo 'Wrong bootstrap bundle ID accepted' >&2
  exit 1
fi
test ! -f "$stage/wrong-id.pkg"
echo 'Logi package validates feed stability and keeps requested app version separate from bootstrap'
