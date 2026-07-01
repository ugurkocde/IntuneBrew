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

# Preserve the existing SHA only when both the version and the URL are unchanged.
# The PKG lives at an evergreen URL, so the hash is tied to the version scraped
# at publish time.
EXISTING_SHA=""
if [ -f "Apps/google_chrome.json" ]; then
    EXISTING_VERSION=$(python3 -c "import json; print(json.load(open('Apps/google_chrome.json')).get('version',''))")
    EXISTING_URL=$(python3 -c "import json; print(json.load(open('Apps/google_chrome.json')).get('url',''))")
    if [ "$EXISTING_VERSION" = "$VERSION" ] && [ "$EXISTING_URL" = "$DOWNLOAD_URL" ]; then
        EXISTING_SHA=$(python3 -c "import json; print(json.load(open('Apps/google_chrome.json')).get('sha',''))")
    fi
fi

SHA_LINE=""
if [ -n "$EXISTING_SHA" ]; then
    SHA_LINE="
  \"sha\": \"$EXISTING_SHA\","
fi

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
  "type": "pkg",$SHA_LINE
  "changelog": "https://chromereleases.googleblog.com/",
  "category": "Browsers",
  "publisher": "Google LLC"
}
EOF

echo "Successfully updated Google Chrome information"
echo "Version: $VERSION"
echo "Download URL: $DOWNLOAD_URL"
