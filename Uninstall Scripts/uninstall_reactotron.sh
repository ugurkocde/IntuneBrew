#!/bin/bash
# Uninstall script for Reactotron
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Reactotron..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Reactotron if running..."
pkill -f "Reactotron" 2>/dev/null || true

# Remove /Applications/Reactotron.app
echo "Removing /Applications/Reactotron.app..."
if [ -d "/Applications/Reactotron.app" ]; then
    rm -rf "/Applications/Reactotron.app" 2>/dev/null || true
elif [ -f "/Applications/Reactotron.app" ]; then
    rm -f "/Applications/Reactotron.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/Reactotron
echo "Removing $HOME/Library/Application Support/Reactotron..."
if [ -d "$HOME/Library/Application Support/Reactotron" ]; then
    rm -rf "$HOME/Library/Application Support/Reactotron" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/Reactotron" ]; then
    rm -f "$HOME/Library/Application Support/Reactotron" 2>/dev/null || true
fi

# Remove $HOME/Library/Logs/Reactotron
echo "Removing $HOME/Library/Logs/Reactotron..."
if [ -d "$HOME/Library/Logs/Reactotron" ]; then
    rm -rf "$HOME/Library/Logs/Reactotron" 2>/dev/null || true
elif [ -f "$HOME/Library/Logs/Reactotron" ]; then
    rm -f "$HOME/Library/Logs/Reactotron" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.reactotron.app.helper.plist
echo "Removing $HOME/Library/Preferences/com.reactotron.app.helper.plist..."
if [ -d "$HOME/Library/Preferences/com.reactotron.app.helper.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.reactotron.app.helper.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.reactotron.app.helper.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.reactotron.app.helper.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.reactotron.app.plist
echo "Removing $HOME/Library/Preferences/com.reactotron.app.plist..."
if [ -d "$HOME/Library/Preferences/com.reactotron.app.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.reactotron.app.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.reactotron.app.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.reactotron.app.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/com.reactotron.app.savedState
echo "Removing $HOME/Library/Saved Application State/com.reactotron.app.savedState..."
if [ -d "$HOME/Library/Saved Application State/com.reactotron.app.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/com.reactotron.app.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/com.reactotron.app.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/com.reactotron.app.savedState" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
