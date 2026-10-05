#!/bin/bash
# Stage Logitech's installer and run its documented silent installation from the PKG.
set -euo pipefail
app_file=$1
version=$2
output=$3
test -f "$app_file/Contents/MacOS/logioptionsplus_installer"
codesign --verify --deep --strict -R '=anchor apple generic and certificate leaf[subject.OU] = "QED4VVPZWA"' "$app_file"
test "$(plutil -extract CFBundleIdentifier raw -o - "$app_file/Contents/Info.plist")" = com.logi.optionsplus.installer
test "$(plutil -extract CFBundleVersion raw -o - "$app_file/Contents/Info.plist")" = "$version"
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
mkdir -p "$stage/payload/usr/local/lib/intunebrew/logitech_options" "$stage/scripts"
ditto "$app_file" "$stage/payload/usr/local/lib/intunebrew/logitech_options/logioptionsplus_installer.app"
cat > "$stage/scripts/postinstall" <<'SCRIPT'
#!/bin/bash
set -euo pipefail
target=${3:-/}
installer="$target/usr/local/lib/intunebrew/logitech_options/logioptionsplus_installer.app/Contents/MacOS/logioptionsplus_installer"
"$installer" --quiet
plist="$target/Applications/logioptionsplus.app/Contents/Info.plist"
test -f "$plist"
bundle_id=$(/usr/bin/plutil -extract CFBundleIdentifier raw -o - "$plist")
test "$bundle_id" = "com.logi.optionsplus"
SCRIPT
chmod 755 "$stage/scripts/postinstall"
pkgbuild --analyze --root "$stage/payload" "$stage/components.plist"
python - "$stage/components.plist" <<'PY'
import plistlib, sys
path = sys.argv[1]
with open(path, 'rb') as stream:
    components = plistlib.load(stream)
for component in components:
    component['BundleIsRelocatable'] = False
with open(path, 'wb') as stream:
    plistlib.dump(components, stream)
PY
pkgbuild --root "$stage/payload" --component-plist "$stage/components.plist" --scripts "$stage/scripts" \
  --identifier com.intunebrew.logitech_options --version "$version" \
  --install-location / "$output"
