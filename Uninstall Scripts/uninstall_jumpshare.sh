#!/bin/bash
# Uninstall script for Jumpshare
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Jumpshare..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Jumpshare if running..."
pkill -f "Jumpshare" 2>/dev/null || true

# Remove /Applications/Jumpshare.app
echo "Removing /Applications/Jumpshare.app..."
if [ -d "/Applications/Jumpshare.app" ]; then
    rm -rf "/Applications/Jumpshare.app" 2>/dev/null || true
elif [ -f "/Applications/Jumpshare.app" ]; then
    rm -f "/Applications/Jumpshare.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Scripts/com.jumpshare.JumpshareLoginHelper
echo "Removing $HOME/Library/Application Scripts/com.jumpshare.JumpshareLoginHelper..."
if [ -d "$HOME/Library/Application Scripts/com.jumpshare.JumpshareLoginHelper" ]; then
    rm -rf "$HOME/Library/Application Scripts/com.jumpshare.JumpshareLoginHelper" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Scripts/com.jumpshare.JumpshareLoginHelper" ]; then
    rm -f "$HOME/Library/Application Scripts/com.jumpshare.JumpshareLoginHelper" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/com.jumpshare.Jumpshare
echo "Removing $HOME/Library/Application Support/com.jumpshare.Jumpshare..."
if [ -d "$HOME/Library/Application Support/com.jumpshare.Jumpshare" ]; then
    rm -rf "$HOME/Library/Application Support/com.jumpshare.Jumpshare" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/com.jumpshare.Jumpshare" ]; then
    rm -f "$HOME/Library/Application Support/com.jumpshare.Jumpshare" 2>/dev/null || true
fi

# Remove $HOME/Library/Containers/com.jumpshare.JumpshareLoginHelper
echo "Removing $HOME/Library/Containers/com.jumpshare.JumpshareLoginHelper..."
if [ -d "$HOME/Library/Containers/com.jumpshare.JumpshareLoginHelper" ]; then
    rm -rf "$HOME/Library/Containers/com.jumpshare.JumpshareLoginHelper" 2>/dev/null || true
elif [ -f "$HOME/Library/Containers/com.jumpshare.JumpshareLoginHelper" ]; then
    rm -f "$HOME/Library/Containers/com.jumpshare.JumpshareLoginHelper" 2>/dev/null || true
fi

# Remove $HOME/Library/Cookies/com.jumpshare.Jumpshare.binarycookies
echo "Removing $HOME/Library/Cookies/com.jumpshare.Jumpshare.binarycookies..."
if [ -d "$HOME/Library/Cookies/com.jumpshare.Jumpshare.binarycookies" ]; then
    rm -rf "$HOME/Library/Cookies/com.jumpshare.Jumpshare.binarycookies" 2>/dev/null || true
elif [ -f "$HOME/Library/Cookies/com.jumpshare.Jumpshare.binarycookies" ]; then
    rm -f "$HOME/Library/Cookies/com.jumpshare.Jumpshare.binarycookies" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.jumpshare.Jumpshare.plist
echo "Removing $HOME/Library/Preferences/com.jumpshare.Jumpshare.plist..."
if [ -d "$HOME/Library/Preferences/com.jumpshare.Jumpshare.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.jumpshare.Jumpshare.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.jumpshare.Jumpshare.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.jumpshare.Jumpshare.plist" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
