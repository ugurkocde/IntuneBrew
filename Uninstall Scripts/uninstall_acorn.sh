#!/bin/bash
# Uninstall script for Acorn
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Acorn..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Acorn if running..."
pkill -f "Acorn" 2>/dev/null || true

# Remove /Applications/Acorn.app
echo "Removing /Applications/Acorn.app..."
if [ -d "/Applications/Acorn.app" ]; then
    rm -rf "/Applications/Acorn.app" 2>/dev/null || true
elif [ -f "/Applications/Acorn.app" ]; then
    rm -f "/Applications/Acorn.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/Acorn
echo "Removing $HOME/Library/Application Support/Acorn..."
if [ -d "$HOME/Library/Application Support/Acorn" ]; then
    rm -rf "$HOME/Library/Application Support/Acorn" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/Acorn" ]; then
    rm -f "$HOME/Library/Application Support/Acorn" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.flyingmeat.Acorn8
echo "Removing $HOME/Library/Caches/com.flyingmeat.Acorn8..."
if [ -d "$HOME/Library/Caches/com.flyingmeat.Acorn8" ]; then
    rm -rf "$HOME/Library/Caches/com.flyingmeat.Acorn8" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.flyingmeat.Acorn8" ]; then
    rm -f "$HOME/Library/Caches/com.flyingmeat.Acorn8" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.flyingmeat.Acorn8.plist
echo "Removing $HOME/Library/Preferences/com.flyingmeat.Acorn8.plist..."
if [ -d "$HOME/Library/Preferences/com.flyingmeat.Acorn8.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.flyingmeat.Acorn8.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.flyingmeat.Acorn8.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.flyingmeat.Acorn8.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/com.flyingmeat.Acorn8.savedState
echo "Removing $HOME/Library/Saved Application State/com.flyingmeat.Acorn8.savedState..."
if [ -d "$HOME/Library/Saved Application State/com.flyingmeat.Acorn8.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/com.flyingmeat.Acorn8.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/com.flyingmeat.Acorn8.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/com.flyingmeat.Acorn8.savedState" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
