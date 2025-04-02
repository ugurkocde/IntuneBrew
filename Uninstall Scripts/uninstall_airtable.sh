#!/bin/bash
# Uninstall script for Airtable
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Airtable..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Airtable if running..."
pkill -f "Airtable" 2>/dev/null || true

# Kill application with bundle ID com.FormaGrid.Airtable if running
echo "Stopping application with bundle ID com.FormaGrid.Airtable if running..."
killall -9 "com.FormaGrid.Airtable" 2>/dev/null || true

# Remove /Applications/Airtable.app
echo "Removing /Applications/Airtable.app..."
if [ -d "/Applications/Airtable.app" ]; then
    rm -rf "/Applications/Airtable.app" 2>/dev/null || true
elif [ -f "/Applications/Airtable.app" ]; then
    rm -f "/Applications/Airtable.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/Airtable
echo "Removing $HOME/Library/Application Support/Airtable..."
if [ -d "$HOME/Library/Application Support/Airtable" ]; then
    rm -rf "$HOME/Library/Application Support/Airtable" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/Airtable" ]; then
    rm -f "$HOME/Library/Application Support/Airtable" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.FormaGrid.Airtable*
echo "Removing $HOME/Library/Caches/com.FormaGrid.Airtable*..."
if [ -d "$HOME/Library/Caches/com.FormaGrid.Airtable*" ]; then
    rm -rf "$HOME/Library/Caches/com.FormaGrid.Airtable*" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.FormaGrid.Airtable*" ]; then
    rm -f "$HOME/Library/Caches/com.FormaGrid.Airtable*" 2>/dev/null || true
fi

# Remove $HOME/Library/Cookies/com.FormaGrid.Airtable.binarycookies
echo "Removing $HOME/Library/Cookies/com.FormaGrid.Airtable.binarycookies..."
if [ -d "$HOME/Library/Cookies/com.FormaGrid.Airtable.binarycookies" ]; then
    rm -rf "$HOME/Library/Cookies/com.FormaGrid.Airtable.binarycookies" 2>/dev/null || true
elif [ -f "$HOME/Library/Cookies/com.FormaGrid.Airtable.binarycookies" ]; then
    rm -f "$HOME/Library/Cookies/com.FormaGrid.Airtable.binarycookies" 2>/dev/null || true
fi

# Remove $HOME/Library/HTTPStorages/com.FormaGrid.Airtable*
echo "Removing $HOME/Library/HTTPStorages/com.FormaGrid.Airtable*..."
if [ -d "$HOME/Library/HTTPStorages/com.FormaGrid.Airtable*" ]; then
    rm -rf "$HOME/Library/HTTPStorages/com.FormaGrid.Airtable*" 2>/dev/null || true
elif [ -f "$HOME/Library/HTTPStorages/com.FormaGrid.Airtable*" ]; then
    rm -f "$HOME/Library/HTTPStorages/com.FormaGrid.Airtable*" 2>/dev/null || true
fi

# Remove $HOME/Library/Logs/Airtable
echo "Removing $HOME/Library/Logs/Airtable..."
if [ -d "$HOME/Library/Logs/Airtable" ]; then
    rm -rf "$HOME/Library/Logs/Airtable" 2>/dev/null || true
elif [ -f "$HOME/Library/Logs/Airtable" ]; then
    rm -f "$HOME/Library/Logs/Airtable" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/ByHost/com.FormaGrid.Airtable.ShipIt.*.plist
echo "Removing $HOME/Library/Preferences/ByHost/com.FormaGrid.Airtable.ShipIt.*.plist..."
if [ -d "$HOME/Library/Preferences/ByHost/com.FormaGrid.Airtable.ShipIt.*.plist" ]; then
    rm -rf "$HOME/Library/Preferences/ByHost/com.FormaGrid.Airtable.ShipIt.*.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/ByHost/com.FormaGrid.Airtable.ShipIt.*.plist" ]; then
    rm -f "$HOME/Library/Preferences/ByHost/com.FormaGrid.Airtable.ShipIt.*.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.FormaGrid.Airtable*.plist
echo "Removing $HOME/Library/Preferences/com.FormaGrid.Airtable*.plist..."
if [ -d "$HOME/Library/Preferences/com.FormaGrid.Airtable*.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.FormaGrid.Airtable*.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.FormaGrid.Airtable*.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.FormaGrid.Airtable*.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/com.FormaGrid.Airtable.savedState
echo "Removing $HOME/Library/Saved Application State/com.FormaGrid.Airtable.savedState..."
if [ -d "$HOME/Library/Saved Application State/com.FormaGrid.Airtable.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/com.FormaGrid.Airtable.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/com.FormaGrid.Airtable.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/com.FormaGrid.Airtable.savedState" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
