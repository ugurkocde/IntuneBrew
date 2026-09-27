#!/bin/bash

# Script to generate Google Chrome app information using the enterprise PKG.
# Chrome deployed from the consumer DMG never registers Google's updater
# (Keystone), so installed browsers cannot update themselves (Issue #203).
# The enterprise PKG installs Keystone system-wide, which fixes self-updates.

# Get the current version from the Homebrew cask API
VERSION=$(curl -s "https://formulae.brew.sh/api/cask/google-chrome.json" | python3 -c "import json,sys; print(json.load(sys.stdin)['version'])")

if [ -z "$VERSION" ]; then
    echo "Error: Could not determine Google Chrome version from Homebrew API" >&2
    exit 1
fi

# Google's evergreen universal enterprise PKG download
DOWNLOAD_URL="https://dl.google.com/dl/chrome/mac/universal/stable/gcem/GoogleChrome.pkg"

# Verify the download URL responds
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -I -L "$DOWNLOAD_URL")
if [ "$HTTP_STATUS" != "200" ]; then
    echo "Error: Google Chrome enterprise PKG URL returned HTTP $HTTP_STATUS" >&2
    exit 1
fi

# The enterprise URL is mutable independently of the Homebrew release record.
# Leave SHA absent so the collector verifies its bytes on every scan (#274).

cat > "Apps/google_chrome.json" << EOF
{
  "name": "Google Chrome",
  "description": "Web browser",
  "version": "$VERSION",
  "url": "$DOWNLOAD_URL",
  "vendor_url": "$DOWNLOAD_URL",
  "bundleId": "com.google.Chrome",
  "homepage": "https://www.google.com/chrome/",
  "fileName": "GoogleChrome-$VERSION.pkg",
  "type": "pkg",
  "changelog": "https://chromereleases.googleblog.com/",
  "category": "Browsers",
  "publisher": "Google LLC"
}
EOF

echo "Successfully updated Google Chrome information"
echo "Version: $VERSION"
echo "Download URL: $DOWNLOAD_URL"
