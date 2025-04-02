#!/bin/bash
# Uninstall script for Badgeify
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Badgeify..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Badgeify if running..."
pkill -f "Badgeify" 2>/dev/null || true

# Kill application with bundle ID studio.techflow.badgeify if running
echo "Stopping application with bundle ID studio.techflow.badgeify if running..."
killall -9 "studio.techflow.badgeify" 2>/dev/null || true

# Remove /Applications/Badgeify.app
echo "Removing /Applications/Badgeify.app..."
if [ -d "/Applications/Badgeify.app" ]; then
    rm -rf "/Applications/Badgeify.app" 2>/dev/null || true
elif [ -f "/Applications/Badgeify.app" ]; then
    rm -f "/Applications/Badgeify.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/studio.techflow.badgeify
echo "Removing $HOME/Library/Application Support/studio.techflow.badgeify..."
if [ -d "$HOME/Library/Application Support/studio.techflow.badgeify" ]; then
    rm -rf "$HOME/Library/Application Support/studio.techflow.badgeify" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/studio.techflow.badgeify" ]; then
    rm -f "$HOME/Library/Application Support/studio.techflow.badgeify" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/studio.techflow.badgeify
echo "Removing $HOME/Library/Caches/studio.techflow.badgeify..."
if [ -d "$HOME/Library/Caches/studio.techflow.badgeify" ]; then
    rm -rf "$HOME/Library/Caches/studio.techflow.badgeify" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/studio.techflow.badgeify" ]; then
    rm -f "$HOME/Library/Caches/studio.techflow.badgeify" 2>/dev/null || true
fi

# Remove $HOME/Library/Logs/studio.techflow.badgeify
echo "Removing $HOME/Library/Logs/studio.techflow.badgeify..."
if [ -d "$HOME/Library/Logs/studio.techflow.badgeify" ]; then
    rm -rf "$HOME/Library/Logs/studio.techflow.badgeify" 2>/dev/null || true
elif [ -f "$HOME/Library/Logs/studio.techflow.badgeify" ]; then
    rm -f "$HOME/Library/Logs/studio.techflow.badgeify" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/studio.techflow.badgeify.plist
echo "Removing $HOME/Library/Preferences/studio.techflow.badgeify.plist..."
if [ -d "$HOME/Library/Preferences/studio.techflow.badgeify.plist" ]; then
    rm -rf "$HOME/Library/Preferences/studio.techflow.badgeify.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/studio.techflow.badgeify.plist" ]; then
    rm -f "$HOME/Library/Preferences/studio.techflow.badgeify.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/WebKit/studio.techflow.badgeify
echo "Removing $HOME/Library/WebKit/studio.techflow.badgeify..."
if [ -d "$HOME/Library/WebKit/studio.techflow.badgeify" ]; then
    rm -rf "$HOME/Library/WebKit/studio.techflow.badgeify" 2>/dev/null || true
elif [ -f "$HOME/Library/WebKit/studio.techflow.badgeify" ]; then
    rm -f "$HOME/Library/WebKit/studio.techflow.badgeify" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
