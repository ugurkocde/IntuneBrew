#!/bin/bash
# Uninstall script for Evernote
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Evernote..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Evernote if running..."
pkill -f "Evernote" 2>/dev/null || true

# Kill application with bundle ID com.evernote.Evernote if running
echo "Stopping application with bundle ID com.evernote.Evernote if running..."
killall -9 "com.evernote.Evernote" 2>/dev/null || true

# Kill application with bundle ID com.evernote.EvernoteHelper if running
echo "Stopping application with bundle ID com.evernote.EvernoteHelper if running..."
killall -9 "com.evernote.EvernoteHelper" 2>/dev/null || true

# Remove /Applications/Evernote.app
echo "Removing /Applications/Evernote.app..."
if [ -d "/Applications/Evernote.app" ]; then
    rm -rf "/Applications/Evernote.app" 2>/dev/null || true
elif [ -f "/Applications/Evernote.app" ]; then
    rm -f "/Applications/Evernote.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/Caches/evernote-client-updater
echo "Removing $HOME/Library/Application Support/Caches/evernote-client-updater..."
if [ -d "$HOME/Library/Application Support/Caches/evernote-client-updater" ]; then
    rm -rf "$HOME/Library/Application Support/Caches/evernote-client-updater" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/Caches/evernote-client-updater" ]; then
    rm -f "$HOME/Library/Application Support/Caches/evernote-client-updater" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/com.evernote.Evernote
echo "Removing $HOME/Library/Application Support/com.evernote.Evernote..."
if [ -d "$HOME/Library/Application Support/com.evernote.Evernote" ]; then
    rm -rf "$HOME/Library/Application Support/com.evernote.Evernote" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/com.evernote.Evernote" ]; then
    rm -f "$HOME/Library/Application Support/com.evernote.Evernote" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/com.evernote.EvernoteHelper
echo "Removing $HOME/Library/Application Support/com.evernote.EvernoteHelper..."
if [ -d "$HOME/Library/Application Support/com.evernote.EvernoteHelper" ]; then
    rm -rf "$HOME/Library/Application Support/com.evernote.EvernoteHelper" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/com.evernote.EvernoteHelper" ]; then
    rm -f "$HOME/Library/Application Support/com.evernote.EvernoteHelper" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/Evernote
echo "Removing $HOME/Library/Application Support/Evernote..."
if [ -d "$HOME/Library/Application Support/Evernote" ]; then
    rm -rf "$HOME/Library/Application Support/Evernote" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/Evernote" ]; then
    rm -f "$HOME/Library/Application Support/Evernote" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.evernote.Evernote
echo "Removing $HOME/Library/Caches/com.evernote.Evernote..."
if [ -d "$HOME/Library/Caches/com.evernote.Evernote" ]; then
    rm -rf "$HOME/Library/Caches/com.evernote.Evernote" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.evernote.Evernote" ]; then
    rm -f "$HOME/Library/Caches/com.evernote.Evernote" 2>/dev/null || true
fi

# Remove $HOME/Library/Cookies/com.evernote.Evernote.binarycookies
echo "Removing $HOME/Library/Cookies/com.evernote.Evernote.binarycookies..."
if [ -d "$HOME/Library/Cookies/com.evernote.Evernote.binarycookies" ]; then
    rm -rf "$HOME/Library/Cookies/com.evernote.Evernote.binarycookies" 2>/dev/null || true
elif [ -f "$HOME/Library/Cookies/com.evernote.Evernote.binarycookies" ]; then
    rm -f "$HOME/Library/Cookies/com.evernote.Evernote.binarycookies" 2>/dev/null || true
fi

# Remove $HOME/Library/Logs/Evernote
echo "Removing $HOME/Library/Logs/Evernote..."
if [ -d "$HOME/Library/Logs/Evernote" ]; then
    rm -rf "$HOME/Library/Logs/Evernote" 2>/dev/null || true
elif [ -f "$HOME/Library/Logs/Evernote" ]; then
    rm -f "$HOME/Library/Logs/Evernote" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.evernote.Evernote.plist
echo "Removing $HOME/Library/Preferences/com.evernote.Evernote.plist..."
if [ -d "$HOME/Library/Preferences/com.evernote.Evernote.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.evernote.Evernote.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.evernote.Evernote.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.evernote.Evernote.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.evernote.EvernoteHelper.plist
echo "Removing $HOME/Library/Preferences/com.evernote.EvernoteHelper.plist..."
if [ -d "$HOME/Library/Preferences/com.evernote.EvernoteHelper.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.evernote.EvernoteHelper.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.evernote.EvernoteHelper.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.evernote.EvernoteHelper.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/com.evernote.Evernote.savedState
echo "Removing $HOME/Library/Saved Application State/com.evernote.Evernote.savedState..."
if [ -d "$HOME/Library/Saved Application State/com.evernote.Evernote.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/com.evernote.Evernote.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/com.evernote.Evernote.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/com.evernote.Evernote.savedState" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
