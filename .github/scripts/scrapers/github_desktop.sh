#!/bin/bash

# Get the latest version from the changelog
VERSION=$(curl -s https://central.github.com/deployments/desktop/desktop/changelog.json | grep -o '"version":"[^"]*' | head -1 | cut -d'"' -f4)

# Download the ZIP file
TEMP_ZIP="temp_github_desktop.zip"
curl -L "https://central.github.com/deployments/desktop/desktop/latest/darwin-arm64" -o "$TEMP_ZIP"

# Create a Python script to process the ZIP file
cat > process_zip.py << EOF
import os
import zipfile
import subprocess
import shutil
from pathlib import Path

def create_dmg_from_app(app_path, dmg_name):
    dmg_path = f"{dmg_name}.dmg"
    staging_dir = Path("temp_dmg")
    staging_dir.mkdir(exist_ok=True)
    
    shutil.copytree(app_path, staging_dir / app_path.name)
    os.symlink("/Applications", staging_dir / "Applications")
    
    subprocess.run([
        'genisoimage',
        '-V', dmg_name,
        '-D',
        '-R',
        '-apple',
        '-no-pad',
        '-o', dmg_path,
        str(staging_dir)
    ], check=True)
    
    shutil.rmtree(staging_dir)
    return dmg_path

# Extract ZIP and process
temp_dir = Path("temp_extract")
temp_dir.mkdir(exist_ok=True)

with zipfile.ZipFile("$TEMP_ZIP", 'r') as zip_ref:
    zip_ref.extractall(temp_dir)

# Find .app directory
app_path = None
for root, dirs, files in os.walk(temp_dir):
    for dir in dirs:
        if dir.endswith('.app'):
            app_path = Path(root) / dir
            break
    if app_path:
        break

if app_path:
    create_dmg_from_app(app_path, "github_desktop")

# Clean up
shutil.rmtree(temp_dir)
EOF

# Run the Python script
python3 process_zip.py

# Clean up the temporary files
rm "$TEMP_ZIP" process_zip.py

# Check if release exists
RELEASE_TAG="github-desktop-latest"
RELEASE_INFO=$(curl -s \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/${GITHUB_REPOSITORY}/releases/tags/${RELEASE_TAG}")

DMG_FILE="github_desktop.dmg"

if [[ $(echo "$RELEASE_INFO" | jq -r '.message // empty') == "Not Found" ]]; then
    # Create new release if it doesn't exist
    echo "Creating new release..."
    RELEASE_RESPONSE=$(curl -L \
      -X POST \
      -H "Accept: application/vnd.github+json" \
      -H "Authorization: Bearer ${GITHUB_TOKEN}" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      "https://api.github.com/repos/${GITHUB_REPOSITORY}/releases" \
      -d "{
        \"tag_name\":\"${RELEASE_TAG}\",
        \"name\":\"GitHub Desktop ${VERSION}\",
        \"draft\":false,
        \"prerelease\":false,
        \"make_latest\":\"true\"
      }")
    RELEASE_ID=$(echo "$RELEASE_RESPONSE" | jq -r '.id')
else
    # Update existing release
    echo "Updating existing release..."
    RELEASE_ID=$(echo "$RELEASE_INFO" | jq -r '.id')
    
    # Delete existing assets
    ASSETS=$(curl -s \
      -H "Accept: application/vnd.github+json" \
      -H "Authorization: Bearer ${GITHUB_TOKEN}" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      "https://api.github.com/repos/${GITHUB_REPOSITORY}/releases/${RELEASE_ID}/assets")
    
    echo "$ASSETS" | jq -r '.[] | .id' | while read ASSET_ID; do
        curl -X DELETE \
          -H "Accept: application/vnd.github+json" \
          -H "Authorization: Bearer ${GITHUB_TOKEN}" \
          -H "X-GitHub-Api-Version: 2022-11-28" \
          "https://api.github.com/repos/${GITHUB_REPOSITORY}/releases/assets/${ASSET_ID}"
    done
    
    # Update release name
    curl -L \
      -X PATCH \
      -H "Accept: application/vnd.github+json" \
      -H "Authorization: Bearer ${GITHUB_TOKEN}" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      "https://api.github.com/repos/${GITHUB_REPOSITORY}/releases/${RELEASE_ID}" \
      -d "{
        \"name\":\"GitHub Desktop ${VERSION}\",
        \"make_latest\":\"true\"
      }"
fi

# Upload DMG file
echo "Uploading DMG file..."
UPLOAD_RESPONSE=$(curl -L \
  -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  -H "Content-Type: application/octet-stream" \
  "https://uploads.github.com/repos/${GITHUB_REPOSITORY}/releases/${RELEASE_ID}/assets?name=${DMG_FILE}" \
  --data-binary "@${DMG_FILE}")

echo "Upload response: $UPLOAD_RESPONSE"

UPLOAD_URL=$(echo "$UPLOAD_RESPONSE" | jq -r '.browser_download_url')

if [[ "$UPLOAD_URL" == "null" ]]; then
    echo "Error uploading DMG file. Response:"
    echo "$UPLOAD_RESPONSE" | jq '.'
    exit 1
fi

# Verify the file exists
echo "Verifying uploaded file..."
VERIFY_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$UPLOAD_URL")
if [[ "$VERIFY_RESPONSE" != "200" ]]; then
    echo "Error: Unable to verify uploaded file at $UPLOAD_URL"
    exit 1
fi

# Create the JSON file
cat > "Apps/github_desktop.json" << EOF
{
  "name": "GitHub Desktop",
  "description": "GitHub Desktop is an application that enables you to interact with GitHub using a GUI",
  "version": "$VERSION",
  "url": "$UPLOAD_URL",
  "bundleId": "com.github.GitHubClient",
  "homepage": "https://desktop.github.com/",
  "fileName": "github_desktop.dmg"
}
EOF

# Add to supported_apps.json
if [ -f "supported_apps.json" ]; then
    if ! grep -q '"github_desktop":' supported_apps.json; then
        sed -i '$ d' supported_apps.json
        if [ "$(wc -l < supported_apps.json)" -gt 1 ]; then
            echo "    ," >> supported_apps.json
        fi
        echo '    "github_desktop": "https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/Apps/github_desktop.json"' >> supported_apps.json
        echo "}" >> supported_apps.json
    fi
fi

# Clean up DMG file
rm "$DMG_FILE"

echo "Successfully updated GitHub Desktop information"
