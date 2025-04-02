#!/bin/bash
# Uninstall script for Rotato
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Rotato..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Rotato if running..."
pkill -f "Rotato" 2>/dev/null || true

# Remove /Applications/Rotato.app
echo "Removing /Applications/Rotato.app..."
if [ -d "/Applications/Rotato.app" ]; then
    rm -rf "/Applications/Rotato.app" 2>/dev/null || true
elif [ -f "/Applications/Rotato.app" ]; then
    rm -f "/Applications/Rotato.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/com.mortenjust.Rendermock
echo "Removing $HOME/Library/Application Support/com.mortenjust.Rendermock..."
if [ -d "$HOME/Library/Application Support/com.mortenjust.Rendermock" ]; then
    rm -rf "$HOME/Library/Application Support/com.mortenjust.Rendermock" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/com.mortenjust.Rendermock" ]; then
    rm -f "$HOME/Library/Application Support/com.mortenjust.Rendermock" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/Rotato
echo "Removing $HOME/Library/Application Support/Rotato..."
if [ -d "$HOME/Library/Application Support/Rotato" ]; then
    rm -rf "$HOME/Library/Application Support/Rotato" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/Rotato" ]; then
    rm -f "$HOME/Library/Application Support/Rotato" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.mortenjust.Rendermock
echo "Removing $HOME/Library/Caches/com.mortenjust.Rendermock..."
if [ -d "$HOME/Library/Caches/com.mortenjust.Rendermock" ]; then
    rm -rf "$HOME/Library/Caches/com.mortenjust.Rendermock" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.mortenjust.Rendermock" ]; then
    rm -f "$HOME/Library/Caches/com.mortenjust.Rendermock" 2>/dev/null || true
fi

# Remove $HOME/Library/HTTPStorages/com.mortenjust.Rendermock
echo "Removing $HOME/Library/HTTPStorages/com.mortenjust.Rendermock..."
if [ -d "$HOME/Library/HTTPStorages/com.mortenjust.Rendermock" ]; then
    rm -rf "$HOME/Library/HTTPStorages/com.mortenjust.Rendermock" 2>/dev/null || true
elif [ -f "$HOME/Library/HTTPStorages/com.mortenjust.Rendermock" ]; then
    rm -f "$HOME/Library/HTTPStorages/com.mortenjust.Rendermock" 2>/dev/null || true
fi

# Remove $HOME/Library/HTTPStorages/com.mortenjust.Rendermock.binarycookies
echo "Removing $HOME/Library/HTTPStorages/com.mortenjust.Rendermock.binarycookies..."
if [ -d "$HOME/Library/HTTPStorages/com.mortenjust.Rendermock.binarycookies" ]; then
    rm -rf "$HOME/Library/HTTPStorages/com.mortenjust.Rendermock.binarycookies" 2>/dev/null || true
elif [ -f "$HOME/Library/HTTPStorages/com.mortenjust.Rendermock.binarycookies" ]; then
    rm -f "$HOME/Library/HTTPStorages/com.mortenjust.Rendermock.binarycookies" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.mortenjust.Rendermock.plist
echo "Removing $HOME/Library/Preferences/com.mortenjust.Rendermock.plist..."
if [ -d "$HOME/Library/Preferences/com.mortenjust.Rendermock.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.mortenjust.Rendermock.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.mortenjust.Rendermock.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.mortenjust.Rendermock.plist" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
