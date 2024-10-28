#!/bin/bash

# Script to fetch latest 1Password information and generate JSON

# Get the latest release build version and version number
RELEASE_PAGE=$(curl -s https://releases.1password.com/mac/)
REL_BUILD_VER=$(echo "$RELEASE_PAGE" | grep "1Password for Mac" | grep -v Beta | head -n 1 | grep href | cut -d = -f 3 | cut -d / -f 3)
VERSION=$(curl -s "https://releases.1password.com/mac/$REL_BUILD_VER/" | grep "Updated to" | cut -d \> -f 78 | cut -d \  -f 3)

# Check if we got a valid version
if [ -z "$VERSION" ]; then
    echo "Error: Could not fetch 1Password version" >&2
    exit 1
fi

# Create JSON output
cat > "Apps/1password.json" << EOF
{
  "name": "1Password",
  "description": "Password manager that keeps all passwords secure behind one",
  "version": "$VERSION",
  "url": "https://downloads.1password.com/mac/1Password.pkg",
  "bundleId": "com.1password.1password",
  "homepage": "https://1password.com/",
  "fileName": "1Password.pkg"
}
EOF

# Add the app to supported_apps.json if it doesn't exist
if [ -f "supported_apps.json" ]; then
    # Check if 1password entry already exists
    if ! grep -q '"1password":' supported_apps.json; then
        # Remove the last closing brace, add the new entry, and close the JSON
        sed -i '$ d' supported_apps.json
        if [ "$(wc -l < supported_apps.json)" -gt 1 ]; then
            echo "    ," >> supported_apps.json
        fi
        echo '    "1password": "https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/Apps/1password.json"' >> supported_apps.json
        echo "}" >> supported_apps.json
    fi
fi

echo "Successfully updated 1Password information"