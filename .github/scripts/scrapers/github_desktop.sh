#!/bin/bash

# Get the latest version from the changelog
VERSION=$(curl -s https://central.github.com/deployments/desktop/desktop/changelog.json | grep -o '"version":"[^"]*' | head -1 | cut -d'"' -f4)

# Download the ZIP file
TEMP_ZIP="temp_github_desktop.zip"
curl -L "https://central.github.com/deployments/desktop/desktop/latest/darwin-arm64" -o "$TEMP_ZIP"

# Process the ZIP and create DMG (assuming process_zip_apps.py is already set up)
python3 .github/scripts/process_zip_apps.py "$TEMP_ZIP" "github_desktop"

# Clean up the temporary ZIP file
rm "$TEMP_ZIP"

# Create the JSON file with the path to the created DMG
cat > "Apps/github_desktop.json" << EOF
{
  "name": "GitHub Desktop",
  "description": "GitHub Desktop is an application that enables you to interact with GitHub using a GUI",
  "version": "$VERSION",
  "url": "https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/Apps/dmg/github_desktop.dmg",
  "bundleId": "com.github.GitHubClient",
  "homepage": "https://desktop.github.com/",
  "fileName": "github_desktop.dmg"
}
EOF

# Add the app to supported_apps.json if it doesn't exist
if [ -f "supported_apps.json" ]; then
    # Check if github_desktop entry already exists
    if ! grep -q '"github_desktop":' supported_apps.json; then
        # Remove the last closing brace, add the new entry, and close the JSON
        sed -i '$ d' supported_apps.json
        if [ "$(wc -l < supported_apps.json)" -gt 1 ]; then
            echo "    ," >> supported_apps.json
        fi
        echo '    "github_desktop": "https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/Apps/github_desktop.json"' >> supported_apps.json
        echo "}" >> supported_apps.json
    fi
fi

# Make sure the DMG file is committed
git add "Apps/dmg/github_desktop.dmg"

echo "Successfully updated GitHub Desktop information"
