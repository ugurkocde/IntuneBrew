#!/bin/bash
# Uninstall script for Fantastical
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Fantastical..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Fantastical if running..."
pkill -f "Fantastical" 2>/dev/null || true

# Unload service com.flexibits.fantastical*.mac.launcher
echo "Unloading service com.flexibits.fantastical*.mac.launcher..."
launchctl unload -w /Library/LaunchAgents/com.flexibits.fantastical*.mac.launcher.plist 2>/dev/null || true
launchctl unload -w /Library/LaunchDaemons/com.flexibits.fantastical*.mac.launcher.plist 2>/dev/null || true
launchctl unload -w ~/Library/LaunchAgents/com.flexibits.fantastical*.mac.launcher.plist 2>/dev/null || true

# Kill application with bundle ID *.com.flexibits.fantastical*.mac.helper if running
echo "Stopping application with bundle ID *.com.flexibits.fantastical*.mac.helper if running..."
killall -9 "*.com.flexibits.fantastical*.mac.helper" 2>/dev/null || true

# Kill application with bundle ID com.flexibits.fantastical*.mac if running
echo "Stopping application with bundle ID com.flexibits.fantastical*.mac if running..."
killall -9 "com.flexibits.fantastical*.mac" 2>/dev/null || true

# Remove /Applications/Fantastical.app
echo "Removing /Applications/Fantastical.app..."
if [ -d "/Applications/Fantastical.app" ]; then
    rm -rf "/Applications/Fantastical.app" 2>/dev/null || true
elif [ -f "/Applications/Fantastical.app" ]; then
    rm -f "/Applications/Fantastical.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Scripts/*.com.flexibits.fantastical*
echo "Removing $HOME/Library/Application Scripts/*.com.flexibits.fantastical*..."
if [ -d "$HOME/Library/Application Scripts/*.com.flexibits.fantastical*" ]; then
    rm -rf "$HOME/Library/Application Scripts/*.com.flexibits.fantastical*" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Scripts/*.com.flexibits.fantastical*" ]; then
    rm -f "$HOME/Library/Application Scripts/*.com.flexibits.fantastical*" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Scripts/com.flexibits.fantastical*
echo "Removing $HOME/Library/Application Scripts/com.flexibits.fantastical*..."
if [ -d "$HOME/Library/Application Scripts/com.flexibits.fantastical*" ]; then
    rm -rf "$HOME/Library/Application Scripts/com.flexibits.fantastical*" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Scripts/com.flexibits.fantastical*" ]; then
    rm -f "$HOME/Library/Application Scripts/com.flexibits.fantastical*" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Scripts/com.flexibits.fbcaldav.*
echo "Removing $HOME/Library/Application Scripts/com.flexibits.fbcaldav.*..."
if [ -d "$HOME/Library/Application Scripts/com.flexibits.fbcaldav.*" ]; then
    rm -rf "$HOME/Library/Application Scripts/com.flexibits.fbcaldav.*" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Scripts/com.flexibits.fbcaldav.*" ]; then
    rm -f "$HOME/Library/Application Scripts/com.flexibits.fbcaldav.*" 2>/dev/null || true
fi

# Remove $HOME/Library/Containers/com.flexibits.fantastical*
echo "Removing $HOME/Library/Containers/com.flexibits.fantastical*..."
if [ -d "$HOME/Library/Containers/com.flexibits.fantastical*" ]; then
    rm -rf "$HOME/Library/Containers/com.flexibits.fantastical*" 2>/dev/null || true
elif [ -f "$HOME/Library/Containers/com.flexibits.fantastical*" ]; then
    rm -f "$HOME/Library/Containers/com.flexibits.fantastical*" 2>/dev/null || true
fi

# Remove $HOME/Library/Containers/com.flexibits.fbcaldav.*
echo "Removing $HOME/Library/Containers/com.flexibits.fbcaldav.*..."
if [ -d "$HOME/Library/Containers/com.flexibits.fbcaldav.*" ]; then
    rm -rf "$HOME/Library/Containers/com.flexibits.fbcaldav.*" 2>/dev/null || true
elif [ -f "$HOME/Library/Containers/com.flexibits.fbcaldav.*" ]; then
    rm -f "$HOME/Library/Containers/com.flexibits.fbcaldav.*" 2>/dev/null || true
fi

# Remove $HOME/Library/Group Containers/*.com.flexibits.fantastical*.mac
echo "Removing $HOME/Library/Group Containers/*.com.flexibits.fantastical*.mac..."
if [ -d "$HOME/Library/Group Containers/*.com.flexibits.fantastical*.mac" ]; then
    rm -rf "$HOME/Library/Group Containers/*.com.flexibits.fantastical*.mac" 2>/dev/null || true
elif [ -f "$HOME/Library/Group Containers/*.com.flexibits.fantastical*.mac" ]; then
    rm -f "$HOME/Library/Group Containers/*.com.flexibits.fantastical*.mac" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.flexibits.fantastical.plist
echo "Removing $HOME/Library/Preferences/com.flexibits.fantastical.plist..."
if [ -d "$HOME/Library/Preferences/com.flexibits.fantastical.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.flexibits.fantastical.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.flexibits.fantastical.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.flexibits.fantastical.plist" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
