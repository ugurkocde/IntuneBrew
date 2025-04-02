#!/bin/bash
# Uninstall script for DaisyDisk
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling DaisyDisk..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping DaisyDisk if running..."
pkill -f "DaisyDisk" 2>/dev/null || true

# Unload service com.daisydiskapp.DaisyDiskAdminHelper
echo "Unloading service com.daisydiskapp.DaisyDiskAdminHelper..."
launchctl unload -w /Library/LaunchAgents/com.daisydiskapp.DaisyDiskAdminHelper.plist 2>/dev/null || true
launchctl unload -w /Library/LaunchDaemons/com.daisydiskapp.DaisyDiskAdminHelper.plist 2>/dev/null || true
launchctl unload -w ~/Library/LaunchAgents/com.daisydiskapp.DaisyDiskAdminHelper.plist 2>/dev/null || true

# Remove /Applications/DaisyDisk.app
echo "Removing /Applications/DaisyDisk.app..."
if [ -d "/Applications/DaisyDisk.app" ]; then
    rm -rf "/Applications/DaisyDisk.app" 2>/dev/null || true
elif [ -f "/Applications/DaisyDisk.app" ]; then
    rm -f "/Applications/DaisyDisk.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/DaisyDisk
echo "Removing $HOME/Library/Application Support/DaisyDisk..."
if [ -d "$HOME/Library/Application Support/DaisyDisk" ]; then
    rm -rf "$HOME/Library/Application Support/DaisyDisk" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/DaisyDisk" ]; then
    rm -f "$HOME/Library/Application Support/DaisyDisk" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.daisydiskapp.DaisyDiskStandAlone
echo "Removing $HOME/Library/Caches/com.daisydiskapp.DaisyDiskStandAlone..."
if [ -d "$HOME/Library/Caches/com.daisydiskapp.DaisyDiskStandAlone" ]; then
    rm -rf "$HOME/Library/Caches/com.daisydiskapp.DaisyDiskStandAlone" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.daisydiskapp.DaisyDiskStandAlone" ]; then
    rm -f "$HOME/Library/Caches/com.daisydiskapp.DaisyDiskStandAlone" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.daisydiskapp.DaisyDiskStandAlone.plist
echo "Removing $HOME/Library/Preferences/com.daisydiskapp.DaisyDiskStandAlone.plist..."
if [ -d "$HOME/Library/Preferences/com.daisydiskapp.DaisyDiskStandAlone.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.daisydiskapp.DaisyDiskStandAlone.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.daisydiskapp.DaisyDiskStandAlone.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.daisydiskapp.DaisyDiskStandAlone.plist" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
