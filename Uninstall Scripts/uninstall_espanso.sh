#!/bin/bash
# Uninstall script for Espanso
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Espanso..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Espanso if running..."
pkill -f "Espanso" 2>/dev/null || true

# Remove /Applications/Espanso.app
echo "Removing /Applications/Espanso.app..."
if [ -d "/Applications/Espanso.app" ]; then
    rm -rf "/Applications/Espanso.app" 2>/dev/null || true
elif [ -f "/Applications/Espanso.app" ]; then
    rm -f "/Applications/Espanso.app" 2>/dev/null || true
fi

# Remove binary /Applications/Espanso.app/Espanso.app/Contents/MacOS/espanso
echo "Removing binary /Applications/Espanso.app/Espanso.app/Contents/MacOS/espanso..."
if [ -f "/Applications/Espanso.app/Espanso.app/Contents/MacOS/espanso" ]; then
    rm -f "/Applications/Espanso.app/Espanso.app/Contents/MacOS/espanso" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/espanso
echo "Removing $HOME/Library/Application Support/espanso..."
if [ -d "$HOME/Library/Application Support/espanso" ]; then
    rm -rf "$HOME/Library/Application Support/espanso" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/espanso" ]; then
    rm -f "$HOME/Library/Application Support/espanso" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/espanso
echo "Removing $HOME/Library/Caches/espanso..."
if [ -d "$HOME/Library/Caches/espanso" ]; then
    rm -rf "$HOME/Library/Caches/espanso" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/espanso" ]; then
    rm -f "$HOME/Library/Caches/espanso" 2>/dev/null || true
fi

# Remove $HOME/Library/LaunchAgents/com.federicoterzi.espanso.plist
echo "Removing $HOME/Library/LaunchAgents/com.federicoterzi.espanso.plist..."
if [ -d "$HOME/Library/LaunchAgents/com.federicoterzi.espanso.plist" ]; then
    rm -rf "$HOME/Library/LaunchAgents/com.federicoterzi.espanso.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/LaunchAgents/com.federicoterzi.espanso.plist" ]; then
    rm -f "$HOME/Library/LaunchAgents/com.federicoterzi.espanso.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.federicoterzi.espanso.plist
echo "Removing $HOME/Library/Preferences/com.federicoterzi.espanso.plist..."
if [ -d "$HOME/Library/Preferences/com.federicoterzi.espanso.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.federicoterzi.espanso.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.federicoterzi.espanso.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.federicoterzi.espanso.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/espanso
echo "Removing $HOME/Library/Preferences/espanso..."
if [ -d "$HOME/Library/Preferences/espanso" ]; then
    rm -rf "$HOME/Library/Preferences/espanso" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/espanso" ]; then
    rm -f "$HOME/Library/Preferences/espanso" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/espanso.plist
echo "Removing $HOME/Library/Preferences/espanso.plist..."
if [ -d "$HOME/Library/Preferences/espanso.plist" ]; then
    rm -rf "$HOME/Library/Preferences/espanso.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/espanso.plist" ]; then
    rm -f "$HOME/Library/Preferences/espanso.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/com.federicoterzi.espanso.savedState
echo "Removing $HOME/Library/Saved Application State/com.federicoterzi.espanso.savedState..."
if [ -d "$HOME/Library/Saved Application State/com.federicoterzi.espanso.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/com.federicoterzi.espanso.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/com.federicoterzi.espanso.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/com.federicoterzi.espanso.savedState" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
