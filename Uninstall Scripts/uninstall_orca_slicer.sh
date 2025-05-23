#!/bin/bash
# Uninstall script for Orca Slicer
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Orca Slicer..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Orca Slicer if running..."
pkill -f "Orca Slicer" 2>/dev/null || true

# Remove /Applications/OrcaSlicer.app
echo "Removing /Applications/OrcaSlicer.app..."
if [ -d "/Applications/OrcaSlicer.app" ]; then
    rm -rf "/Applications/OrcaSlicer.app" 2>/dev/null || true
elif [ -f "/Applications/OrcaSlicer.app" ]; then
    rm -f "/Applications/OrcaSlicer.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/OrcaSlicer
echo "Removing $HOME/Library/Application Support/OrcaSlicer..."
if [ -d "$HOME/Library/Application Support/OrcaSlicer" ]; then
    rm -rf "$HOME/Library/Application Support/OrcaSlicer" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/OrcaSlicer" ]; then
    rm -f "$HOME/Library/Application Support/OrcaSlicer" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.softfever3d.orca-slicer
echo "Removing $HOME/Library/Caches/com.softfever3d.orca-slicer..."
if [ -d "$HOME/Library/Caches/com.softfever3d.orca-slicer" ]; then
    rm -rf "$HOME/Library/Caches/com.softfever3d.orca-slicer" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.softfever3d.orca-slicer" ]; then
    rm -f "$HOME/Library/Caches/com.softfever3d.orca-slicer" 2>/dev/null || true
fi

# Remove $HOME/Library/HTTPStorages/com.softfever3d.orcaslicer.binarycookies
echo "Removing $HOME/Library/HTTPStorages/com.softfever3d.orcaslicer.binarycookies..."
if [ -d "$HOME/Library/HTTPStorages/com.softfever3d.orcaslicer.binarycookies" ]; then
    rm -rf "$HOME/Library/HTTPStorages/com.softfever3d.orcaslicer.binarycookies" 2>/dev/null || true
elif [ -f "$HOME/Library/HTTPStorages/com.softfever3d.orcaslicer.binarycookies" ]; then
    rm -f "$HOME/Library/HTTPStorages/com.softfever3d.orcaslicer.binarycookies" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.softfever3d.orca-slicer.plist
echo "Removing $HOME/Library/Preferences/com.softfever3d.orca-slicer.plist..."
if [ -d "$HOME/Library/Preferences/com.softfever3d.orca-slicer.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.softfever3d.orca-slicer.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.softfever3d.orca-slicer.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.softfever3d.orca-slicer.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/com.softfever3d.orca-slicer.savedState
echo "Removing $HOME/Library/Saved Application State/com.softfever3d.orca-slicer.savedState..."
if [ -d "$HOME/Library/Saved Application State/com.softfever3d.orca-slicer.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/com.softfever3d.orca-slicer.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/com.softfever3d.orca-slicer.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/com.softfever3d.orca-slicer.savedState" 2>/dev/null || true
fi

# Remove $HOME/Library/WebKit/com.softfever3d.orca-slicer
echo "Removing $HOME/Library/WebKit/com.softfever3d.orca-slicer..."
if [ -d "$HOME/Library/WebKit/com.softfever3d.orca-slicer" ]; then
    rm -rf "$HOME/Library/WebKit/com.softfever3d.orca-slicer" 2>/dev/null || true
elif [ -f "$HOME/Library/WebKit/com.softfever3d.orca-slicer" ]; then
    rm -f "$HOME/Library/WebKit/com.softfever3d.orca-slicer" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
