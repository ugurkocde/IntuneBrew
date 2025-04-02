#!/bin/bash
# Uninstall script for Spline
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Spline..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Spline if running..."
pkill -f "Spline" 2>/dev/null || true

# Remove /Applications/Spline.app
echo "Removing /Applications/Spline.app..."
if [ -d "/Applications/Spline.app" ]; then
    rm -rf "/Applications/Spline.app" 2>/dev/null || true
elif [ -f "/Applications/Spline.app" ]; then
    rm -f "/Applications/Spline.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.design.spline.plist
echo "Removing $HOME/Library/Preferences/com.design.spline.plist..."
if [ -d "$HOME/Library/Preferences/com.design.spline.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.design.spline.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.design.spline.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.design.spline.plist" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
