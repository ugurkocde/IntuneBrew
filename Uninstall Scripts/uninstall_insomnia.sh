#!/bin/bash
# Uninstall script for Insomnia
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Insomnia..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Insomnia if running..."
pkill -f "Insomnia" 2>/dev/null || true

# Remove /Applications/Insomnia.app
echo "Removing /Applications/Insomnia.app..."
if [ -d "/Applications/Insomnia.app" ]; then
    rm -rf "/Applications/Insomnia.app" 2>/dev/null || true
elif [ -f "/Applications/Insomnia.app" ]; then
    rm -f "/Applications/Insomnia.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/Insomnia
echo "Removing $HOME/Library/Application Support/Insomnia..."
if [ -d "$HOME/Library/Application Support/Insomnia" ]; then
    rm -rf "$HOME/Library/Application Support/Insomnia" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/Insomnia" ]; then
    rm -f "$HOME/Library/Application Support/Insomnia" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.insomnia.app
echo "Removing $HOME/Library/Caches/com.insomnia.app..."
if [ -d "$HOME/Library/Caches/com.insomnia.app" ]; then
    rm -rf "$HOME/Library/Caches/com.insomnia.app" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.insomnia.app" ]; then
    rm -f "$HOME/Library/Caches/com.insomnia.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.insomnia.app.ShipIt
echo "Removing $HOME/Library/Caches/com.insomnia.app.ShipIt..."
if [ -d "$HOME/Library/Caches/com.insomnia.app.ShipIt" ]; then
    rm -rf "$HOME/Library/Caches/com.insomnia.app.ShipIt" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.insomnia.app.ShipIt" ]; then
    rm -f "$HOME/Library/Caches/com.insomnia.app.ShipIt" 2>/dev/null || true
fi

# Remove $HOME/Library/Cookies/com.insomnia.app.binarycookies
echo "Removing $HOME/Library/Cookies/com.insomnia.app.binarycookies..."
if [ -d "$HOME/Library/Cookies/com.insomnia.app.binarycookies" ]; then
    rm -rf "$HOME/Library/Cookies/com.insomnia.app.binarycookies" 2>/dev/null || true
elif [ -f "$HOME/Library/Cookies/com.insomnia.app.binarycookies" ]; then
    rm -f "$HOME/Library/Cookies/com.insomnia.app.binarycookies" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/ByHost/com.insomnia.app.ShipIt.*.plist
echo "Removing $HOME/Library/Preferences/ByHost/com.insomnia.app.ShipIt.*.plist..."
if [ -d "$HOME/Library/Preferences/ByHost/com.insomnia.app.ShipIt.*.plist" ]; then
    rm -rf "$HOME/Library/Preferences/ByHost/com.insomnia.app.ShipIt.*.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/ByHost/com.insomnia.app.ShipIt.*.plist" ]; then
    rm -f "$HOME/Library/Preferences/ByHost/com.insomnia.app.ShipIt.*.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.insomnia.app.helper.plist
echo "Removing $HOME/Library/Preferences/com.insomnia.app.helper.plist..."
if [ -d "$HOME/Library/Preferences/com.insomnia.app.helper.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.insomnia.app.helper.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.insomnia.app.helper.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.insomnia.app.helper.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.insomnia.app.plist
echo "Removing $HOME/Library/Preferences/com.insomnia.app.plist..."
if [ -d "$HOME/Library/Preferences/com.insomnia.app.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.insomnia.app.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.insomnia.app.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.insomnia.app.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/com.insomnia.app.savedState
echo "Removing $HOME/Library/Saved Application State/com.insomnia.app.savedState..."
if [ -d "$HOME/Library/Saved Application State/com.insomnia.app.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/com.insomnia.app.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/com.insomnia.app.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/com.insomnia.app.savedState" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
