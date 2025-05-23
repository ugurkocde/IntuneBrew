#!/bin/bash
# Uninstall script for Hyperkey
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Hyperkey..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Hyperkey if running..."
pkill -f "Hyperkey" 2>/dev/null || true

# Kill application with bundle ID com.knollsoft.Hyperkey if running
echo "Stopping application with bundle ID com.knollsoft.Hyperkey if running..."
killall -9 "com.knollsoft.Hyperkey" 2>/dev/null || true

# Remove /Applications/Hyperkey.app
echo "Removing /Applications/Hyperkey.app..."
if [ -d "/Applications/Hyperkey.app" ]; then
    rm -rf "/Applications/Hyperkey.app" 2>/dev/null || true
elif [ -f "/Applications/Hyperkey.app" ]; then
    rm -f "/Applications/Hyperkey.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Scripts/com.knollsoft.HyperkeyLauncher
echo "Removing $HOME/Library/Application Scripts/com.knollsoft.HyperkeyLauncher..."
if [ -d "$HOME/Library/Application Scripts/com.knollsoft.HyperkeyLauncher" ]; then
    rm -rf "$HOME/Library/Application Scripts/com.knollsoft.HyperkeyLauncher" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Scripts/com.knollsoft.HyperkeyLauncher" ]; then
    rm -f "$HOME/Library/Application Scripts/com.knollsoft.HyperkeyLauncher" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/Hyperkey
echo "Removing $HOME/Library/Application Support/Hyperkey..."
if [ -d "$HOME/Library/Application Support/Hyperkey" ]; then
    rm -rf "$HOME/Library/Application Support/Hyperkey" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/Hyperkey" ]; then
    rm -f "$HOME/Library/Application Support/Hyperkey" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.knollsoft.Hyperkey
echo "Removing $HOME/Library/Caches/com.knollsoft.Hyperkey..."
if [ -d "$HOME/Library/Caches/com.knollsoft.Hyperkey" ]; then
    rm -rf "$HOME/Library/Caches/com.knollsoft.Hyperkey" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.knollsoft.Hyperkey" ]; then
    rm -f "$HOME/Library/Caches/com.knollsoft.Hyperkey" 2>/dev/null || true
fi

# Remove $HOME/Library/Containers/com.knollsoft.HyperkeyLauncher
echo "Removing $HOME/Library/Containers/com.knollsoft.HyperkeyLauncher..."
if [ -d "$HOME/Library/Containers/com.knollsoft.HyperkeyLauncher" ]; then
    rm -rf "$HOME/Library/Containers/com.knollsoft.HyperkeyLauncher" 2>/dev/null || true
elif [ -f "$HOME/Library/Containers/com.knollsoft.HyperkeyLauncher" ]; then
    rm -f "$HOME/Library/Containers/com.knollsoft.HyperkeyLauncher" 2>/dev/null || true
fi

# Remove $HOME/Library/Cookies/com.knollsoft.Hyperkey.binarycookies
echo "Removing $HOME/Library/Cookies/com.knollsoft.Hyperkey.binarycookies..."
if [ -d "$HOME/Library/Cookies/com.knollsoft.Hyperkey.binarycookies" ]; then
    rm -rf "$HOME/Library/Cookies/com.knollsoft.Hyperkey.binarycookies" 2>/dev/null || true
elif [ -f "$HOME/Library/Cookies/com.knollsoft.Hyperkey.binarycookies" ]; then
    rm -f "$HOME/Library/Cookies/com.knollsoft.Hyperkey.binarycookies" 2>/dev/null || true
fi

# Remove $HOME/Library/HTTPStorages/com.knollsoft.Hyperkey
echo "Removing $HOME/Library/HTTPStorages/com.knollsoft.Hyperkey..."
if [ -d "$HOME/Library/HTTPStorages/com.knollsoft.Hyperkey" ]; then
    rm -rf "$HOME/Library/HTTPStorages/com.knollsoft.Hyperkey" 2>/dev/null || true
elif [ -f "$HOME/Library/HTTPStorages/com.knollsoft.Hyperkey" ]; then
    rm -f "$HOME/Library/HTTPStorages/com.knollsoft.Hyperkey" 2>/dev/null || true
fi

# Remove $HOME/Library/HTTPStorages/com.knollsoft.Hyperkey.binarycookies
echo "Removing $HOME/Library/HTTPStorages/com.knollsoft.Hyperkey.binarycookies..."
if [ -d "$HOME/Library/HTTPStorages/com.knollsoft.Hyperkey.binarycookies" ]; then
    rm -rf "$HOME/Library/HTTPStorages/com.knollsoft.Hyperkey.binarycookies" 2>/dev/null || true
elif [ -f "$HOME/Library/HTTPStorages/com.knollsoft.Hyperkey.binarycookies" ]; then
    rm -f "$HOME/Library/HTTPStorages/com.knollsoft.Hyperkey.binarycookies" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.knollsoft.Hyperkey.plist
echo "Removing $HOME/Library/Preferences/com.knollsoft.Hyperkey.plist..."
if [ -d "$HOME/Library/Preferences/com.knollsoft.Hyperkey.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.knollsoft.Hyperkey.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.knollsoft.Hyperkey.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.knollsoft.Hyperkey.plist" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
