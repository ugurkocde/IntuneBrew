#!/bin/bash
# Uninstall script for Raycast
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Raycast..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Raycast if running..."
pkill -f "Raycast" 2>/dev/null || true

# Kill application with bundle ID com.raycast.macos if running
echo "Stopping application with bundle ID com.raycast.macos if running..."
killall -9 "com.raycast.macos" 2>/dev/null || true

# Remove /Applications/Raycast.app
echo "Removing /Applications/Raycast.app..."
if [ -d "/Applications/Raycast.app" ]; then
    rm -rf "/Applications/Raycast.app" 2>/dev/null || true
elif [ -f "/Applications/Raycast.app" ]; then
    rm -f "/Applications/Raycast.app" 2>/dev/null || true
fi

# Remove $HOME/.config/raycast
echo "Removing $HOME/.config/raycast..."
if [ -d "$HOME/.config/raycast" ]; then
    rm -rf "$HOME/.config/raycast" 2>/dev/null || true
elif [ -f "$HOME/.config/raycast" ]; then
    rm -f "$HOME/.config/raycast" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Scripts/com.raycast.macos.BrowserExtension
echo "Removing $HOME/Library/Application Scripts/com.raycast.macos.BrowserExtension..."
if [ -d "$HOME/Library/Application Scripts/com.raycast.macos.BrowserExtension" ]; then
    rm -rf "$HOME/Library/Application Scripts/com.raycast.macos.BrowserExtension" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Scripts/com.raycast.macos.BrowserExtension" ]; then
    rm -f "$HOME/Library/Application Scripts/com.raycast.macos.BrowserExtension" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/com.raycast.macos
echo "Removing $HOME/Library/Application Support/com.raycast.macos..."
if [ -d "$HOME/Library/Application Support/com.raycast.macos" ]; then
    rm -rf "$HOME/Library/Application Support/com.raycast.macos" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/com.raycast.macos" ]; then
    rm -f "$HOME/Library/Application Support/com.raycast.macos" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.raycast.macos
echo "Removing $HOME/Library/Caches/com.raycast.macos..."
if [ -d "$HOME/Library/Caches/com.raycast.macos" ]; then
    rm -rf "$HOME/Library/Caches/com.raycast.macos" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.raycast.macos" ]; then
    rm -f "$HOME/Library/Caches/com.raycast.macos" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/SentryCrash/Raycast
echo "Removing $HOME/Library/Caches/SentryCrash/Raycast..."
if [ -d "$HOME/Library/Caches/SentryCrash/Raycast" ]; then
    rm -rf "$HOME/Library/Caches/SentryCrash/Raycast" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/SentryCrash/Raycast" ]; then
    rm -f "$HOME/Library/Caches/SentryCrash/Raycast" 2>/dev/null || true
fi

# Remove $HOME/Library/Containers/com.raycast.macos.BrowserExtension
echo "Removing $HOME/Library/Containers/com.raycast.macos.BrowserExtension..."
if [ -d "$HOME/Library/Containers/com.raycast.macos.BrowserExtension" ]; then
    rm -rf "$HOME/Library/Containers/com.raycast.macos.BrowserExtension" 2>/dev/null || true
elif [ -f "$HOME/Library/Containers/com.raycast.macos.BrowserExtension" ]; then
    rm -f "$HOME/Library/Containers/com.raycast.macos.BrowserExtension" 2>/dev/null || true
fi

# Remove $HOME/Library/Cookies/com.raycast.macos.binarycookies
echo "Removing $HOME/Library/Cookies/com.raycast.macos.binarycookies..."
if [ -d "$HOME/Library/Cookies/com.raycast.macos.binarycookies" ]; then
    rm -rf "$HOME/Library/Cookies/com.raycast.macos.binarycookies" 2>/dev/null || true
elif [ -f "$HOME/Library/Cookies/com.raycast.macos.binarycookies" ]; then
    rm -f "$HOME/Library/Cookies/com.raycast.macos.binarycookies" 2>/dev/null || true
fi

# Remove $HOME/Library/HTTPStorages/com.raycast.macos
echo "Removing $HOME/Library/HTTPStorages/com.raycast.macos..."
if [ -d "$HOME/Library/HTTPStorages/com.raycast.macos" ]; then
    rm -rf "$HOME/Library/HTTPStorages/com.raycast.macos" 2>/dev/null || true
elif [ -f "$HOME/Library/HTTPStorages/com.raycast.macos" ]; then
    rm -f "$HOME/Library/HTTPStorages/com.raycast.macos" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.raycast.macos.plist
echo "Removing $HOME/Library/Preferences/com.raycast.macos.plist..."
if [ -d "$HOME/Library/Preferences/com.raycast.macos.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.raycast.macos.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.raycast.macos.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.raycast.macos.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/WebKit/com.raycast.macos
echo "Removing $HOME/Library/WebKit/com.raycast.macos..."
if [ -d "$HOME/Library/WebKit/com.raycast.macos" ]; then
    rm -rf "$HOME/Library/WebKit/com.raycast.macos" 2>/dev/null || true
elif [ -f "$HOME/Library/WebKit/com.raycast.macos" ]; then
    rm -f "$HOME/Library/WebKit/com.raycast.macos" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
