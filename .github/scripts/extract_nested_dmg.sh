#!/bin/bash
# Expand a disk image wrapped inside a vendor archive, without running its code.
set -euo pipefail
extracted_dir=$1
if find "$extracted_dir" \( -name '*.app' -o -name '*.pkg' \) ! -path '*/__MACOSX/*' -print -quit | grep -q .; then
  exit 0
fi
dmg=$(find "$extracted_dir" -type f -iname '*.dmg' ! -path '*/__MACOSX/*' -print -quit)
[ -n "$dmg" ] || exit 0
mount_dir=$(mktemp -d)
mounted=false
cleanup() {
  if [ "$mounted" = true ]; then hdiutil detach "$mount_dir" -force >/dev/null 2>&1 || true; fi
  rmdir "$mount_dir" 2>/dev/null || true
}
trap cleanup EXIT
hdiutil attach "$dmg" -readonly -nobrowse -mountpoint "$mount_dir" >/dev/null
mounted=true
payload=$(find "$mount_dir" -type d -name '*.app' -print -quit)
if [ -z "$payload" ]; then
  payload=$(find "$mount_dir" -name '*.pkg' -print -quit)
fi
if [ -z "$payload" ]; then
  echo 'Nested disk image contains no app or installer package' >&2
  exit 1
fi
ditto "$payload" "$extracted_dir/$(basename "$payload")"
