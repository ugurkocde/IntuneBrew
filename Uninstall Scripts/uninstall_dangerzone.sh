#!/bin/bash
# Uninstall script for Dangerzone
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Dangerzone..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Dangerzone if running..."
pkill -f "Dangerzone" 2>/dev/null || true

# Remove /Applications/Dangerzone.app
echo "Removing /Applications/Dangerzone.app..."
if [ -d "/Applications/Dangerzone.app" ]; then
    rm -rf "/Applications/Dangerzone.app" 2>/dev/null || true
elif [ -f "/Applications/Dangerzone.app" ]; then
    rm -f "/Applications/Dangerzone.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/dangerzone
echo "Removing $HOME/Library/Application Support/dangerzone..."
if [ -d "$HOME/Library/Application Support/dangerzone" ]; then
    rm -rf "$HOME/Library/Application Support/dangerzone" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/dangerzone" ]; then
    rm -f "$HOME/Library/Application Support/dangerzone" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/press.freedom.dangerzone.savedState
echo "Removing $HOME/Library/Saved Application State/press.freedom.dangerzone.savedState..."
if [ -d "$HOME/Library/Saved Application State/press.freedom.dangerzone.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/press.freedom.dangerzone.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/press.freedom.dangerzone.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/press.freedom.dangerzone.savedState" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
