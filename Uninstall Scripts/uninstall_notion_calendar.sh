#!/bin/bash
# Uninstall script for Notion Calendar
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Notion Calendar..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Notion Calendar if running..."
pkill -f "Notion Calendar" 2>/dev/null || true

# Remove /Applications/Notion Calendar.app
echo "Removing /Applications/Notion Calendar.app..."
if [ -d "/Applications/Notion Calendar.app" ]; then
    rm -rf "/Applications/Notion Calendar.app" 2>/dev/null || true
elif [ -f "/Applications/Notion Calendar.app" ]; then
    rm -f "/Applications/Notion Calendar.app" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
