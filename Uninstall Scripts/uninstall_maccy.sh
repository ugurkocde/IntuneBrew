#!/bin/bash
# Uninstall script for Maccy
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Maccy..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Maccy if running..."
pkill -f "Maccy" 2>/dev/null || true

# Kill application with bundle ID org.p0deje.Maccy if running
echo "Stopping application with bundle ID org.p0deje.Maccy if running..."
killall -9 "org.p0deje.Maccy" 2>/dev/null || true

# Remove /Applications/Maccy.app
echo "Removing /Applications/Maccy.app..."
if [ -d "/Applications/Maccy.app" ]; then
    rm -rf "/Applications/Maccy.app" 2>/dev/null || true
elif [ -f "/Applications/Maccy.app" ]; then
    rm -f "/Applications/Maccy.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Scripts/org.p0deje.Maccy
echo "Removing $HOME/Library/Application Scripts/org.p0deje.Maccy..."
if [ -d "$HOME/Library/Application Scripts/org.p0deje.Maccy" ]; then
    rm -rf "$HOME/Library/Application Scripts/org.p0deje.Maccy" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Scripts/org.p0deje.Maccy" ]; then
    rm -f "$HOME/Library/Application Scripts/org.p0deje.Maccy" 2>/dev/null || true
fi

# Remove $HOME/Library/Containers/org.p0deje.Maccy
echo "Removing $HOME/Library/Containers/org.p0deje.Maccy..."
if [ -d "$HOME/Library/Containers/org.p0deje.Maccy" ]; then
    rm -rf "$HOME/Library/Containers/org.p0deje.Maccy" 2>/dev/null || true
elif [ -f "$HOME/Library/Containers/org.p0deje.Maccy" ]; then
    rm -f "$HOME/Library/Containers/org.p0deje.Maccy" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/org.p0deje.Maccy.plist
echo "Removing $HOME/Library/Preferences/org.p0deje.Maccy.plist..."
if [ -d "$HOME/Library/Preferences/org.p0deje.Maccy.plist" ]; then
    rm -rf "$HOME/Library/Preferences/org.p0deje.Maccy.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/org.p0deje.Maccy.plist" ]; then
    rm -f "$HOME/Library/Preferences/org.p0deje.Maccy.plist" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
