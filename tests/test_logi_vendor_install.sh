#!/bin/bash
# Only run on disposable CI Macs: installs the real Logitech app as root.
set -euo pipefail
test "${CI:-}" = true
root=$(cd "$(dirname "$0")/.." && pwd)
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
curl --fail --silent --show-error --location 'https://formulae.brew.sh/api/cask/logi-options+.json' > "$stage/cask.json"
version=$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$stage/cask.json")
url=$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["url"])' "$stage/cask.json")
bash "$root/.github/scripts/download_vendor.sh" "$url" "$stage/vendor.zip"
bash "$root/.github/scripts/extract_vendor_zip.sh" "$stage/vendor.zip" "$stage/source"
app=$(find "$stage/source" -type d -name '*.app' ! -path '*/__MACOSX/*' -print -quit)
codesign --verify --deep --strict "$app"
bash "$root/.github/scripts/package_logi_options.sh" "$app" "$version" "$stage/logi.pkg"
sudo installer -pkg "$stage/logi.pkg" -target /
test "$(plutil -extract CFBundleIdentifier raw -o - /Applications/logioptionsplus.app/Contents/Info.plist)" = com.logi.optionsplus
echo 'Real Logi Options+ installed successfully through the PKG postinstall'
