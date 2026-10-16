#!/bin/bash
# Stage Logitech's installer and run its documented silent installation from the PKG.
set -euo pipefail
app_file=$1
version=$2
output=$3
fail() { echo "Logitech package refused: $*" >&2; exit 1; }
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail 'Malformed requested version'
test -f "$app_file/Contents/MacOS/logioptionsplus_installer" || fail 'Installer executable missing'
codesign --verify --deep --strict -R '=anchor apple generic and certificate leaf[subject.OU] = "QED4VVPZWA"' "$app_file" || fail 'Installer signature differs'
test "$(plutil -extract CFBundleIdentifier raw -o - "$app_file/Contents/Info.plist")" = com.logi.optionsplus.installer || fail 'Installer bundle identity differs'
bootstrap_version=$(plutil -extract CFBundleVersion raw -o - "$app_file/Contents/Info.plist") || fail 'Bootstrap version missing'
printf 'Logitech bootstrap version %s; requested application version %s\n' "$bootstrap_version" "$version"
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
check_feed() {
  curl --fail --silent --show-error --location --max-time 30 \
    'https://updates.optionsplus.logitechg.com/pipeline/v2/update/optionsplus5/osx/public/update.json' \
    > "$stage/feed.json" || fail 'Update feed unavailable'
  python - "$stage/feed.json" "$version" <<'PY' || fail 'Update feed does not match requested application version'
import json, sys
try:
    with open(sys.argv[1]) as stream:
        version = json.load(stream)['version']
except (OSError, ValueError, KeyError, TypeError):
    raise SystemExit(1)
raise SystemExit(0 if version == sys.argv[2] else 1)
PY
}
check_feed
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
  --install-location / "$stage/result.pkg"
# The bootstrap fetches the app online; its own version is not the app version.
# Publish the local output only if the requested feed version stayed stable.
check_feed
mv "$stage/result.pkg" "$output"
