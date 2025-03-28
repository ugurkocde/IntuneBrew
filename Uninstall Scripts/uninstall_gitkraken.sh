#!/bin/bash
# Uninstall script for GitKraken
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling GitKraken..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping GitKraken if running..."
pkill -f "GitKraken" 2>/dev/null || true

# Remove /Applications/GitKraken.app
echo "Removing /Applications/GitKraken.app..."
if [ -d "/Applications/GitKraken.app" ]; then
    rm -rf "/Applications/GitKraken.app" 2>/dev/null || true
elif [ -f "/Applications/GitKraken.app" ]; then
    rm -f "/Applications/GitKraken.app" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
