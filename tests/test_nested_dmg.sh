#!/bin/bash
set -euo pipefail
script=$(cd "$(dirname "$0")/.." && pwd)/.github/scripts/extract_nested_dmg.sh
fixture=$(mktemp -d)
trap 'rm -rf "$fixture"' EXIT
mkdir -p "$fixture/source/Example.app/Contents" "$fixture/extracted/nested"
printf 'fixture payload' > "$fixture/source/Example.app/Contents/example"
hdiutil create -quiet -srcfolder "$fixture/source" -format UDZO "$fixture/extracted/nested/vendor.dmg"
bash "$script" "$fixture/extracted"
cmp "$fixture/source/Example.app/Contents/example" "$fixture/extracted/Example.app/Contents/example"
# An already extracted application takes precedence over a malformed nested image.
printf 'invalid image' > "$fixture/extracted/nested/vendor.dmg"
bash "$script" "$fixture/extracted"
rm -rf "$fixture/extracted/Example.app"
if bash "$script" "$fixture/extracted"; then
  echo 'Malformed disk image unexpectedly succeeded' >&2
  exit 1
fi
printf 'Nested DMG extraction checks passed\n'

# ZIPs can contain more than 64 KiB of trailing vendor data after their directory.
zip_script="$(dirname "$script")/extract_vendor_zip.sh"
(cd "$fixture/source" && zip -qr "$fixture/vendor.zip" .)
dd if=/dev/zero bs=1024 count=103 >> "$fixture/vendor.zip" 2>/dev/null
bash "$zip_script" "$fixture/vendor.zip" "$fixture/unzipped"
cmp "$fixture/source/Example.app/Contents/example" "$fixture/unzipped/Example.app/Contents/example"
printf 'not an archive' > "$fixture/broken.zip"
if bash "$zip_script" "$fixture/broken.zip" "$fixture/broken-output"; then
  echo 'Malformed ZIP unexpectedly succeeded' >&2
  exit 1
fi
