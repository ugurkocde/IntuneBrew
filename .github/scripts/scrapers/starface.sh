#!/bin/bash

# Script to fetch latest Starface information and generate JSON

# Fetch the appcast XML
XML_CONTENT=$(curl -s -L "https://www.starface-cdn.de/starface/clients/mac/appcast.xml")

# Check if we got valid XML
if [ -z "$XML_CONTENT" ]; then
    echo "Error: Could not fetch Starface appcast XML" >&2
    exit 1
fi

# Extract version from sparkle:shortVersionString
VERSION=$(echo "$XML_CONTENT" | grep -o '<sparkle:shortVersionString>[^<]*</sparkle:shortVersionString>' | head -1 | sed 's/<[^>]*>//g')

# Extract download URL from enclosure
DOWNLOAD_URL=$(echo "$XML_CONTENT" | grep -o 'url="[^"]*"' | head -1 | sed 's/url="//;s/"//')

# Extract English description - get the content between description tags with xml:lang="en"
DESCRIPTION=$(echo "$XML_CONTENT" | awk '/<description xml:lang="en">/{flag=1; next} /<\/description>/{if(flag) exit} flag' | tr -d '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | head -1)

# If no English description, try to get the general description
if [ -z "$DESCRIPTION" ]; then
    DESCRIPTION="STARFACE UCC Client for macOS - Unified Communications and Collaboration"
fi

# Check if we got valid data
if [ -z "$VERSION" ] || [ -z "$DOWNLOAD_URL" ]; then
    echo "Error: Could not extract version or download URL from Starface XML" >&2
    exit 1
fi

# Extract filename from URL
FILENAME=$(basename "$DOWNLOAD_URL")

# Create JSON output
cat > "Apps/starface.json" << EOF
{
  "name": "Starface",
  "description": "$DESCRIPTION",
  "version": "$VERSION",
  "url": "$DOWNLOAD_URL",
  "bundleId": "de.starface.STARFACE",
  "homepage": "https://www.starface.com/",
  "fileName": "$FILENAME"
}
EOF

# Add the app to supported_apps.json if it doesn't exist
if [ -f "supported_apps.json" ]; then
    # Check if starface entry already exists
    if ! grep -q '"starface":' supported_apps.json; then
        # Remove the last closing brace, add the new entry, and close the JSON
        sed -i '' '$ d' supported_apps.json
        if [ "$(wc -l < supported_apps.json)" -gt 1 ]; then
            echo "    ," >> supported_apps.json
        fi
        echo '    "starface": "https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/Apps/starface.json"' >> supported_apps.json
        echo "}" >> supported_apps.json
    fi
fi

echo "Successfully updated Starface information"
echo "Version: $VERSION"
echo "Download URL: $DOWNLOAD_URL"