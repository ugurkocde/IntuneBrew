#!/bin/bash
# Uninstall script for Godspeed
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Godspeed..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Godspeed if running..."
pkill -f "Godspeed" 2>/dev/null || true

# Remove /Applications/Godspeed.app
echo "Removing /Applications/Godspeed.app..."
if [ -d "/Applications/Godspeed.app" ]; then
    rm -rf "/Applications/Godspeed.app" 2>/dev/null || true
elif [ -f "/Applications/Godspeed.app" ]; then
    rm -f "/Applications/Godspeed.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.godspeedapp.*
echo "Removing $HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.godspeedapp.*..."
if [ -d "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.godspeedapp.*" ]; then
    rm -rf "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.godspeedapp.*" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.godspeedapp.*" ]; then
    rm -f "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.godspeedapp.*" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/Godspeed
echo "Removing $HOME/Library/Application Support/Godspeed..."
if [ -d "$HOME/Library/Application Support/Godspeed" ]; then
    rm -rf "$HOME/Library/Application Support/Godspeed" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/Godspeed" ]; then
    rm -f "$HOME/Library/Application Support/Godspeed" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.godspeedapp.Godspeed
echo "Removing $HOME/Library/Caches/com.godspeedapp.Godspeed..."
if [ -d "$HOME/Library/Caches/com.godspeedapp.Godspeed" ]; then
    rm -rf "$HOME/Library/Caches/com.godspeedapp.Godspeed" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.godspeedapp.Godspeed" ]; then
    rm -f "$HOME/Library/Caches/com.godspeedapp.Godspeed" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.godspeedapp.Godspeed.ShipIt
echo "Removing $HOME/Library/Caches/com.godspeedapp.Godspeed.ShipIt..."
if [ -d "$HOME/Library/Caches/com.godspeedapp.Godspeed.ShipIt" ]; then
    rm -rf "$HOME/Library/Caches/com.godspeedapp.Godspeed.ShipIt" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.godspeedapp.Godspeed.ShipIt" ]; then
    rm -f "$HOME/Library/Caches/com.godspeedapp.Godspeed.ShipIt" 2>/dev/null || true
fi

# Remove $HOME/Library/HTTPStorages/com.godspeedapp.Godspeed
echo "Removing $HOME/Library/HTTPStorages/com.godspeedapp.Godspeed..."
if [ -d "$HOME/Library/HTTPStorages/com.godspeedapp.Godspeed" ]; then
    rm -rf "$HOME/Library/HTTPStorages/com.godspeedapp.Godspeed" 2>/dev/null || true
elif [ -f "$HOME/Library/HTTPStorages/com.godspeedapp.Godspeed" ]; then
    rm -f "$HOME/Library/HTTPStorages/com.godspeedapp.Godspeed" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.godspeedapp.Godspeed.plist
echo "Removing $HOME/Library/Preferences/com.godspeedapp.Godspeed.plist..."
if [ -d "$HOME/Library/Preferences/com.godspeedapp.Godspeed.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.godspeedapp.Godspeed.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.godspeedapp.Godspeed.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.godspeedapp.Godspeed.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/com.godspeedapp.Godspeed.savedState
echo "Removing $HOME/Library/Saved Application State/com.godspeedapp.Godspeed.savedState..."
if [ -d "$HOME/Library/Saved Application State/com.godspeedapp.Godspeed.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/com.godspeedapp.Godspeed.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/com.godspeedapp.Godspeed.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/com.godspeedapp.Godspeed.savedState" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
