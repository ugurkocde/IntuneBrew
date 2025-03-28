#!/bin/bash
# Uninstall script for Mountain Duck
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Mountain Duck..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Mountain Duck if running..."
pkill -f "Mountain Duck" 2>/dev/null || true

# Remove /Applications/Mountain Duck.app
echo "Removing /Applications/Mountain Duck.app..."
if [ -d "/Applications/Mountain Duck.app" ]; then
    rm -rf "/Applications/Mountain Duck.app" 2>/dev/null || true
elif [ -f "/Applications/Mountain Duck.app" ]; then
    rm -f "/Applications/Mountain Duck.app" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
