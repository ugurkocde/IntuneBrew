#!/bin/bash
# Uninstall script for Windsurf
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Windsurf..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Windsurf if running..."
pkill -f "Windsurf" 2>/dev/null || true

# Unload service com.exafunction.windsurf.ShipIt
echo "Unloading service com.exafunction.windsurf.ShipIt..."
launchctl unload -w /Library/LaunchAgents/com.exafunction.windsurf.ShipIt.plist 2>/dev/null || true
launchctl unload -w /Library/LaunchDaemons/com.exafunction.windsurf.ShipIt.plist 2>/dev/null || true
launchctl unload -w ~/Library/LaunchAgents/com.exafunction.windsurf.ShipIt.plist 2>/dev/null || true

# Kill application with bundle ID com.exafunction.windsurf if running
echo "Stopping application with bundle ID com.exafunction.windsurf if running..."
killall -9 "com.exafunction.windsurf" 2>/dev/null || true

# Remove /Applications/Windsurf.app
echo "Removing /Applications/Windsurf.app..."
if [ -d "/Applications/Windsurf.app" ]; then
    rm -rf "/Applications/Windsurf.app" 2>/dev/null || true
elif [ -f "/Applications/Windsurf.app" ]; then
    rm -f "/Applications/Windsurf.app" 2>/dev/null || true
fi

# Remove binary /Applications/Windsurf.app/Windsurf.app/Contents/Resources/app/bin/windsurf
echo "Removing binary /Applications/Windsurf.app/Windsurf.app/Contents/Resources/app/bin/windsurf..."
if [ -f "/Applications/Windsurf.app/Windsurf.app/Contents/Resources/app/bin/windsurf" ]; then
    rm -f "/Applications/Windsurf.app/Windsurf.app/Contents/Resources/app/bin/windsurf" 2>/dev/null || true
fi

# Remove $HOME/.windsurf
echo "Removing $HOME/.windsurf..."
if [ -d "$HOME/.windsurf" ]; then
    rm -rf "$HOME/.windsurf" 2>/dev/null || true
elif [ -f "$HOME/.windsurf" ]; then
    rm -f "$HOME/.windsurf" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.exafunction.windsurf.sfl*
echo "Removing $HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.exafunction.windsurf.sfl*..."
if [ -d "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.exafunction.windsurf.sfl*" ]; then
    rm -rf "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.exafunction.windsurf.sfl*" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.exafunction.windsurf.sfl*" ]; then
    rm -f "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.exafunction.windsurf.sfl*" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/Windsurf
echo "Removing $HOME/Library/Application Support/Windsurf..."
if [ -d "$HOME/Library/Application Support/Windsurf" ]; then
    rm -rf "$HOME/Library/Application Support/Windsurf" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/Windsurf" ]; then
    rm -f "$HOME/Library/Application Support/Windsurf" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.exafunction.windsurf
echo "Removing $HOME/Library/Caches/com.exafunction.windsurf..."
if [ -d "$HOME/Library/Caches/com.exafunction.windsurf" ]; then
    rm -rf "$HOME/Library/Caches/com.exafunction.windsurf" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.exafunction.windsurf" ]; then
    rm -f "$HOME/Library/Caches/com.exafunction.windsurf" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.exafunction.windsurf.ShipIt
echo "Removing $HOME/Library/Caches/com.exafunction.windsurf.ShipIt..."
if [ -d "$HOME/Library/Caches/com.exafunction.windsurf.ShipIt" ]; then
    rm -rf "$HOME/Library/Caches/com.exafunction.windsurf.ShipIt" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.exafunction.windsurf.ShipIt" ]; then
    rm -f "$HOME/Library/Caches/com.exafunction.windsurf.ShipIt" 2>/dev/null || true
fi

# Remove $HOME/Library/HTTPStorages/com.exafunction.windsurf
echo "Removing $HOME/Library/HTTPStorages/com.exafunction.windsurf..."
if [ -d "$HOME/Library/HTTPStorages/com.exafunction.windsurf" ]; then
    rm -rf "$HOME/Library/HTTPStorages/com.exafunction.windsurf" 2>/dev/null || true
elif [ -f "$HOME/Library/HTTPStorages/com.exafunction.windsurf" ]; then
    rm -f "$HOME/Library/HTTPStorages/com.exafunction.windsurf" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.exafunction.windsurf.plist
echo "Removing $HOME/Library/Preferences/com.exafunction.windsurf.plist..."
if [ -d "$HOME/Library/Preferences/com.exafunction.windsurf.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.exafunction.windsurf.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.exafunction.windsurf.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.exafunction.windsurf.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/com.exafunction.windsurf.savedState
echo "Removing $HOME/Library/Saved Application State/com.exafunction.windsurf.savedState..."
if [ -d "$HOME/Library/Saved Application State/com.exafunction.windsurf.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/com.exafunction.windsurf.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/com.exafunction.windsurf.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/com.exafunction.windsurf.savedState" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
