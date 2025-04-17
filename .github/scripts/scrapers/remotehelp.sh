#!/bin/bash

# Script to fetch latest Remote Help information and generate JSON

# Get the latest version number from Microsoft's documentation and clean up HTML tags
VERSION=$(curl -s -L "https://learn.microsoft.com/en-us/intune/intune-service/fundamentals/remote-help-macos" |
         grep -o "<strong>[0-9.]*</strong>" |
         sed 's/<[^>]*>//g')

# Check if we got a valid version
if [ -z "$VERSION" ]; then
    echo "Error: Could not fetch Remote Help version" >&2
    exit 1
fi

# Create JSON output
cat > "Apps/remotehelp.json" << EOF
{
  "name": "Remote Help",
  "description": "Microsoft Remote Help for secure help desk connections with role-based access controls",
  "version": "$VERSION",
  "url": "https://aka.ms/downloadremotehelpmacos",
  "bundleId": "com.microsoft.remotehelp",
  "homepage": "https://learn.microsoft.com/en-us/mem/intune/fundamentals/remote-help-macos",
  "fileName": "RemoteHelp.pkg"
}
EOF

# Add the app to supported_apps.json if it doesn't exist
if [ -f "supported_apps.json" ]; then
    # Check if remotehelp entry already exists
    if ! grep -q '"remotehelp":' supported_apps.json; then
        # Remove the last closing brace, add the new entry, and close the JSON
        sed -i '$ d' supported_apps.json
        if [ "$(wc -l < supported_apps.json)" -gt 1 ]; then
            echo "    ," >> supported_apps.json
        fi
        echo '    "remotehelp": "https://raw.githubusercontent.com/ugurkocde/IntuneBrew/main/Apps/remotehelp.json"' >> supported_apps.json
        echo "}" >> supported_apps.json
    fi
fi

echo "Successfully updated Remote Help information"