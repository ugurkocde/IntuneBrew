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
