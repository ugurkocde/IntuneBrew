#!/bin/bash
# Uninstall script for CleanShot
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling CleanShot..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping CleanShot if running..."
pkill -f "CleanShot" 2>/dev/null || true

# Kill application with bundle ID pl.maketheweb.cleanshotx if running
echo "Stopping application with bundle ID pl.maketheweb.cleanshotx if running..."
killall -9 "pl.maketheweb.cleanshotx" 2>/dev/null || true

# Remove /Applications/CleanShot X.app
echo "Removing /Applications/CleanShot X.app..."
if [ -d "/Applications/CleanShot X.app" ]; then
    rm -rf "/Applications/CleanShot X.app" 2>/dev/null || true
elif [ -f "/Applications/CleanShot X.app" ]; then
    rm -f "/Applications/CleanShot X.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/CleanShot
echo "Removing $HOME/Library/Application Support/CleanShot..."
if [ -d "$HOME/Library/Application Support/CleanShot" ]; then
    rm -rf "$HOME/Library/Application Support/CleanShot" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/CleanShot" ]; then
    rm -f "$HOME/Library/Application Support/CleanShot" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/pl.maketheweb.cleanshotx
echo "Removing $HOME/Library/Caches/pl.maketheweb.cleanshotx..."
if [ -d "$HOME/Library/Caches/pl.maketheweb.cleanshotx" ]; then
    rm -rf "$HOME/Library/Caches/pl.maketheweb.cleanshotx" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/pl.maketheweb.cleanshotx" ]; then
    rm -f "$HOME/Library/Caches/pl.maketheweb.cleanshotx" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/SentryCrash/CleanShot X
echo "Removing $HOME/Library/Caches/SentryCrash/CleanShot X..."
if [ -d "$HOME/Library/Caches/SentryCrash/CleanShot X" ]; then
    rm -rf "$HOME/Library/Caches/SentryCrash/CleanShot X" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/SentryCrash/CleanShot X" ]; then
    rm -f "$HOME/Library/Caches/SentryCrash/CleanShot X" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.getcleanshot.app.plist
echo "Removing $HOME/Library/Preferences/com.getcleanshot.app.plist..."
if [ -d "$HOME/Library/Preferences/com.getcleanshot.app.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.getcleanshot.app.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.getcleanshot.app.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.getcleanshot.app.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/pl.maketheweb.cleanshotx.plist
echo "Removing $HOME/Library/Preferences/pl.maketheweb.cleanshotx.plist..."
if [ -d "$HOME/Library/Preferences/pl.maketheweb.cleanshotx.plist" ]; then
    rm -rf "$HOME/Library/Preferences/pl.maketheweb.cleanshotx.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/pl.maketheweb.cleanshotx.plist" ]; then
    rm -f "$HOME/Library/Preferences/pl.maketheweb.cleanshotx.plist" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
