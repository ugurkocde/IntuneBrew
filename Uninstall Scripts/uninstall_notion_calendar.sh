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

# Remove $HOME/Library/Application Support/Notion Calendar
echo "Removing $HOME/Library/Application Support/Notion Calendar..."
if [ -d "$HOME/Library/Application Support/Notion Calendar" ]; then
    rm -rf "$HOME/Library/Application Support/Notion Calendar" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/Notion Calendar" ]; then
    rm -f "$HOME/Library/Application Support/Notion Calendar" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.cron.electron.plist
echo "Removing $HOME/Library/Preferences/com.cron.electron.plist..."
if [ -d "$HOME/Library/Preferences/com.cron.electron.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.cron.electron.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.cron.electron.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.cron.electron.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/com.cron.electron.savedState
echo "Removing $HOME/Library/Saved Application State/com.cron.electron.savedState..."
if [ -d "$HOME/Library/Saved Application State/com.cron.electron.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/com.cron.electron.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/com.cron.electron.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/com.cron.electron.savedState" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
