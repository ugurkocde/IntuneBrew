#!/bin/bash
# Script to update uninstall scripts for macOS applications
# This script is part of the IntuneBrew project

# Set error handling
set -e

echo "IntuneBrew - Updating macOS Uninstall Scripts"
echo "=============================================="

# Check if Python is installed
if ! command -v python3 &>/dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if requests module is installed
python3 -c "import requests" 2>/dev/null || {
    echo "Installing required Python module: requests"
    pip3 install requests
}

# Run the script to generate uninstall scripts
echo "Generating uninstall scripts..."
python3 generate_uninstall_scripts.py

# Count the number of scripts generated
script_count=$(find "Uninstall Scripts" -name "uninstall_*.sh" | wc -l)
echo "Successfully generated $script_count uninstall scripts."

echo "Done! Uninstall scripts are available in the 'Uninstall Scripts' folder."
