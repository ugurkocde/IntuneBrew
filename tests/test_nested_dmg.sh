#!/bin/bash
set -euo pipefail
script=$(cd "$(dirname "$0")/.." && pwd)/.github/scripts/extract_nested_dmg.sh
fixture=$(mktemp -d)
trap 'rm -rf "$fixture"' EXIT
mkdir -p "$fixture/source/Example.app/Contents" "$fixture/extracted/nested"
printf 'fixture payload' > "$fixture/source/Example.app/Contents/example"
hdiutil create -quiet -srcfolder "$fixture/source" -format UDZO "$fixture/extracted/nested/vendor.dmg"
# A raw vendor DMG can be downloaded without a .dmg extension and reported by
# file(1) as zlib compressed. Stage it through the same extractor as the build.
udif_script="$(dirname "$script")/is_udif_dmg.sh"
cp "$fixture/extracted/nested/vendor.dmg" "$fixture/vendor.download"
bash "$udif_script" "$fixture/vendor.download"
mkdir "$fixture/raw-extracted"
mv "$fixture/vendor.download" "$fixture/raw-extracted/vendor.dmg"
bash "$script" "$fixture/raw-extracted"
cmp "$fixture/source/Example.app/Contents/example" "$fixture/raw-extracted/Example.app/Contents/example"
printf 'koly' > "$fixture/truncated.download"
if bash "$udif_script" "$fixture/truncated.download"; then
  echo 'Truncated UDIF trailer unexpectedly accepted' >&2
  exit 1
fi
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
if bash "$udif_script" "$fixture/vendor.zip"; then
  echo 'ZIP unexpectedly routed through DMG extraction' >&2
  exit 1
fi
dd if=/dev/zero bs=1024 count=103 >> "$fixture/vendor.zip" 2>/dev/null
bash "$zip_script" "$fixture/vendor.zip" "$fixture/unzipped"
cmp "$fixture/source/Example.app/Contents/example" "$fixture/unzipped/Example.app/Contents/example"
printf 'not an archive' > "$fixture/broken.zip"
if bash "$zip_script" "$fixture/broken.zip" "$fixture/broken-output"; then
  echo 'Malformed ZIP unexpectedly succeeded' >&2
  exit 1
fi
