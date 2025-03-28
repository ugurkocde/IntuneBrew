#!/bin/bash
# Uninstall script for Beeper
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Beeper..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Beeper if running..."
pkill -f "Beeper" 2>/dev/null || true

# Remove /Applications/Beeper.app
echo "Removing /Applications/Beeper.app..."
if [ -d "/Applications/Beeper.app" ]; then
    rm -rf "/Applications/Beeper.app" 2>/dev/null || true
elif [ -f "/Applications/Beeper.app" ]; then
    rm -f "/Applications/Beeper.app" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
