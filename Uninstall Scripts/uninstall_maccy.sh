#!/bin/bash
# Uninstall script for Maccy
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Maccy..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Maccy if running..."
pkill -f "Maccy" 2>/dev/null || true

# Remove /Applications/Maccy.app
echo "Removing /Applications/Maccy.app..."
if [ -d "/Applications/Maccy.app" ]; then
    rm -rf "/Applications/Maccy.app" 2>/dev/null || true
elif [ -f "/Applications/Maccy.app" ]; then
    rm -f "/Applications/Maccy.app" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
