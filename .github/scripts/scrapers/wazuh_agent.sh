#!/bin/bash

# Script to fetch the latest Wazuh Agent information (Issue #97).
# Wazuh is not distributed via Homebrew, so the version is taken from the
# latest GitHub release and the package from the official Wazuh repository.

# Get the latest release tag from GitHub (e.g. v4.14.1)
VERSION=$(curl -s "https://api.github.com/repos/wazuh/wazuh/releases/latest" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tag_name','').lstrip('v'))")

if [ -z "$VERSION" ]; then
    echo "Error: Could not determine latest Wazuh version from GitHub API" >&2
    exit 1
fi

# Official package repository URL (Apple Silicon build)
DOWNLOAD_URL="https://packages.wazuh.com/4.x/macos/wazuh-agent-$VERSION-1.arm64.pkg"

# Verify the download URL responds before writing anything
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -I -L "$DOWNLOAD_URL")
if [ "$HTTP_STATUS" != "200" ]; then
    echo "Error: Wazuh Agent PKG URL returned HTTP $HTTP_STATUS for version $VERSION" >&2
    exit 1
fi

# Preserve the existing SHA only when both the version and the URL are unchanged
EXISTING_SHA=""
if [ -f "Apps/wazuh_agent.json" ]; then
    EXISTING_VERSION=$(python3 -c "import json; print(json.load(open('Apps/wazuh_agent.json')).get('version',''))")
    EXISTING_URL=$(python3 -c "import json; print(json.load(open('Apps/wazuh_agent.json')).get('url',''))")
    if [ "$EXISTING_VERSION" = "$VERSION" ] && [ "$EXISTING_URL" = "$DOWNLOAD_URL" ]; then
        EXISTING_SHA=$(python3 -c "import json; print(json.load(open('Apps/wazuh_agent.json')).get('sha',''))")
    fi
fi

SHA_LINE=""
if [ -n "$EXISTING_SHA" ]; then
    SHA_LINE="
  \"sha\": \"$EXISTING_SHA\","
fi

cat > "Apps/wazuh_agent.json" << EOF
{
  "name": "Wazuh Agent",
  "description": "Endpoint security agent for the Wazuh open source security platform. Requires the WAZUH_MANAGER address to be configured after installation, for example via a post-install script.",
  "version": "$VERSION",
  "url": "$DOWNLOAD_URL",
  "vendor_url": "$DOWNLOAD_URL",
  "bundleId": "com.wazuh.pkg.wazuh-agent",
  "homepage": "https://wazuh.com/",
  "fileName": "wazuh-agent-$VERSION-1.arm64.pkg",
  "type": "pkg",$SHA_LINE
  "category": "Security",
  "publisher": "Wazuh, Inc."
}
EOF

echo "Successfully updated Wazuh Agent information"
echo "Version: $VERSION"
echo "Download URL: $DOWNLOAD_URL"
