#!/bin/bash
# Uninstall script for Acorn
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Acorn..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Acorn if running..."
pkill -f "Acorn" 2>/dev/null || true

# Remove /Applications/Acorn.app
echo "Removing /Applications/Acorn.app..."
if [ -d "/Applications/Acorn.app" ]; then
    rm -rf "/Applications/Acorn.app" 2>/dev/null || true
elif [ -f "/Applications/Acorn.app" ]; then
    rm -f "/Applications/Acorn.app" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
