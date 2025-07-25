#!/bin/bash
# Uninstall script for SilentKnight
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling SilentKnight..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping SilentKnight if running..."
pkill -f "SilentKnight" 2>/dev/null || true

# Remove /Applications/silentknight212/SilentKnight.app
echo "Removing /Applications/silentknight212/SilentKnight.app..."
if [ -d "/Applications/silentknight212/SilentKnight.app" ]; then
    rm -rf "/Applications/silentknight212/SilentKnight.app" 2>/dev/null || true
elif [ -f "/Applications/silentknight212/SilentKnight.app" ]; then
    rm -f "/Applications/silentknight212/SilentKnight.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/co.eclecticlight.silentknight.sfl*
echo "Removing $HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/co.eclecticlight.silentknight.sfl*..."
if [ -d "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/co.eclecticlight.silentknight.sfl*" ]; then
    rm -rf "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/co.eclecticlight.silentknight.sfl*" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/co.eclecticlight.silentknight.sfl*" ]; then
    rm -f "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/co.eclecticlight.silentknight.sfl*" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/co.eclecticlight.SilentKnight
echo "Removing $HOME/Library/Caches/co.eclecticlight.SilentKnight..."
if [ -d "$HOME/Library/Caches/co.eclecticlight.SilentKnight" ]; then
    rm -rf "$HOME/Library/Caches/co.eclecticlight.SilentKnight" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/co.eclecticlight.SilentKnight" ]; then
    rm -f "$HOME/Library/Caches/co.eclecticlight.SilentKnight" 2>/dev/null || true
fi

# Remove $HOME/Library/HTTPStorages/co.eclecticlight.SilentKnight
echo "Removing $HOME/Library/HTTPStorages/co.eclecticlight.SilentKnight..."
if [ -d "$HOME/Library/HTTPStorages/co.eclecticlight.SilentKnight" ]; then
    rm -rf "$HOME/Library/HTTPStorages/co.eclecticlight.SilentKnight" 2>/dev/null || true
elif [ -f "$HOME/Library/HTTPStorages/co.eclecticlight.SilentKnight" ]; then
    rm -f "$HOME/Library/HTTPStorages/co.eclecticlight.SilentKnight" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/co.eclecticlight.SilentKnight.plist
echo "Removing $HOME/Library/Preferences/co.eclecticlight.SilentKnight.plist..."
if [ -d "$HOME/Library/Preferences/co.eclecticlight.SilentKnight.plist" ]; then
    rm -rf "$HOME/Library/Preferences/co.eclecticlight.SilentKnight.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/co.eclecticlight.SilentKnight.plist" ]; then
    rm -f "$HOME/Library/Preferences/co.eclecticlight.SilentKnight.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/co.eclecticlight.SilentKnight.savedState
echo "Removing $HOME/Library/Saved Application State/co.eclecticlight.SilentKnight.savedState..."
if [ -d "$HOME/Library/Saved Application State/co.eclecticlight.SilentKnight.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/co.eclecticlight.SilentKnight.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/co.eclecticlight.SilentKnight.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/co.eclecticlight.SilentKnight.savedState" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
