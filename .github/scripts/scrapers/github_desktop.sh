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
    dmg_path = f"Apps/dmg/{dmg_name}.dmg"
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

echo "Successfully updated GitHub Desktop information"
