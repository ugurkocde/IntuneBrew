#!/bin/bash

# Azure Storage settings
AZURE_STORAGE_ACCOUNT="${AZURE_STORAGE_ACCOUNT}"
AZURE_CONTAINER="${AZURE_CONTAINER}"
AZURE_SAS_TOKEN="${AZURE_SAS_TOKEN}"

# Verify Azure settings
if [ -z "$AZURE_STORAGE_ACCOUNT" ] || [ -z "$AZURE_CONTAINER" ] || [ -z "$AZURE_SAS_TOKEN" ]; then
    echo "Error: Azure Storage settings are not properly configured"
    echo "AZURE_STORAGE_ACCOUNT: ${AZURE_STORAGE_ACCOUNT:-not set}"
    echo "AZURE_CONTAINER: ${AZURE_CONTAINER:-not set}"
    echo "AZURE_SAS_TOKEN: ${AZURE_SAS_TOKEN:+set but not shown}"
    exit 1
fi

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

DMG_FILE="github_desktop.dmg"
BLOB_NAME="github-desktop/${VERSION}/${DMG_FILE}"

# Upload to Azure Blob Storage
echo "Uploading DMG to Azure Storage..."
echo "Storage Account: $AZURE_STORAGE_ACCOUNT"
echo "Container: $AZURE_CONTAINER"
echo "Blob Name: $BLOB_NAME"

# Ensure SAS token starts with '?'
if [[ ! "$AZURE_SAS_TOKEN" =~ ^\? ]]; then
    AZURE_SAS_TOKEN="?${AZURE_SAS_TOKEN}"
fi

# Remove any leading slashes from container name and blob name
AZURE_CONTAINER=$(echo "$AZURE_CONTAINER" | sed 's:^/::')
BLOB_NAME=$(echo "$BLOB_NAME" | sed 's:^/::')

UPLOAD_URL="https://${AZURE_STORAGE_ACCOUNT}.blob.core.windows.net/${AZURE_CONTAINER}/${BLOB_NAME}${AZURE_SAS_TOKEN}"

echo "Attempting upload..."
UPLOAD_RESULT=$(curl -s -w "%{http_code}" -X PUT \
     -H "x-ms-blob-type: BlockBlob" \
     -H "Content-Type: application/octet-stream" \
     -H "x-ms-version: 2020-04-08" \
     --data-binary "@${DMG_FILE}" \
     "${UPLOAD_URL}")

HTTP_CODE=${UPLOAD_RESULT: -3}
RESPONSE_BODY=${UPLOAD_RESULT:0:${#UPLOAD_RESULT}-3}

echo "HTTP Response Code: $HTTP_CODE"
if [ "$HTTP_CODE" != "201" ]; then
    echo "Error uploading to Azure Storage. Response:"
    echo "$RESPONSE_BODY"
    exit 1
fi

echo "Upload successful!"

# Create the public URL without the SAS token
PUBLIC_URL="https://${AZURE_STORAGE_ACCOUNT}.blob.core.windows.net/${AZURE_CONTAINER}/github-desktop/${VERSION}/${DMG_FILE}"

# Create the JSON file with the public URL
cat > "Apps/github_desktop.json" << EOF
{
  "name": "GitHub Desktop",
  "description": "GitHub Desktop is an application that enables you to interact with GitHub using a GUI",
  "version": "$VERSION",
  "url": "$PUBLIC_URL",
  "bundleId": "com.github.GitHubClient",
  "homepage": "https://desktop.github.com/",
  "fileName": "github_desktop.dmg"
}
EOF

# Add to supported_apps.json if it doesn't exist
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
