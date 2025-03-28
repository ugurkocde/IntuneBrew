#!/bin/bash
# Uninstall script for Fantastical
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Fantastical..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Fantastical if running..."
pkill -f "Fantastical" 2>/dev/null || true

# Remove /Applications/Fantastical.app
echo "Removing /Applications/Fantastical.app..."
if [ -d "/Applications/Fantastical.app" ]; then
    rm -rf "/Applications/Fantastical.app" 2>/dev/null || true
elif [ -f "/Applications/Fantastical.app" ]; then
    rm -f "/Applications/Fantastical.app" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
