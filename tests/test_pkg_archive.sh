#!/bin/bash
set -euo pipefail
fixture=$(mktemp -d)
trap 'rm -rf "$fixture"' EXIT
mkdir -p "$fixture/input/__MACOSX" "$fixture/payload"
printf 'AppleDouble metadata' > "$fixture/input/._Installer.pkg"
printf 'AppleDouble metadata' > "$fixture/input/__MACOSX/Installer.pkg"
printf 'fixture' > "$fixture/payload/example.txt"
pkgbuild --root "$fixture/payload" --identifier com.intunebrew.test.archive --version 1 --install-location /tmp/intunebrew-fixture "$fixture/input/Installer.pkg" >/dev/null
package=$(find "$fixture/input" -name '*.pkg' ! -name '._*' ! -path '*/__MACOSX/*' -type f -print -quit)
[[ "$package" == "$fixture/input/Installer.pkg" ]]
xar -tf "$package" >/dev/null
if xar -tf "$fixture/input/._Installer.pkg" >/dev/null 2>&1; then
  echo 'AppleDouble sidecar incorrectly accepted as an installer' >&2
  exit 1
fi
echo 'Package discovery ignores metadata and archive validation rejects sidecars.'
