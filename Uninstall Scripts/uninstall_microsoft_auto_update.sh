#!/bin/bash
# Uninstall script for Microsoft Auto Update
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Microsoft Auto Update..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Microsoft Auto Update if running..."
pkill -f "Microsoft Auto Update" 2>/dev/null || true

# Unload service com.microsoft.autoupdate.helper
echo "Unloading service com.microsoft.autoupdate.helper..."
launchctl unload -w /Library/LaunchAgents/com.microsoft.autoupdate.helper.plist 2>/dev/null || true
launchctl unload -w /Library/LaunchDaemons/com.microsoft.autoupdate.helper.plist 2>/dev/null || true
launchctl unload -w ~/Library/LaunchAgents/com.microsoft.autoupdate.helper.plist 2>/dev/null || true

# Unload service com.microsoft.autoupdate.helpertool
echo "Unloading service com.microsoft.autoupdate.helpertool..."
launchctl unload -w /Library/LaunchAgents/com.microsoft.autoupdate.helpertool.plist 2>/dev/null || true
launchctl unload -w /Library/LaunchDaemons/com.microsoft.autoupdate.helpertool.plist 2>/dev/null || true
launchctl unload -w ~/Library/LaunchAgents/com.microsoft.autoupdate.helpertool.plist 2>/dev/null || true

# Unload service com.microsoft.update.agent
echo "Unloading service com.microsoft.update.agent..."
launchctl unload -w /Library/LaunchAgents/com.microsoft.update.agent.plist 2>/dev/null || true
launchctl unload -w /Library/LaunchDaemons/com.microsoft.update.agent.plist 2>/dev/null || true
launchctl unload -w ~/Library/LaunchAgents/com.microsoft.update.agent.plist 2>/dev/null || true

# Kill application with bundle ID com.microsoft.autoupdate.fba if running
echo "Stopping application with bundle ID com.microsoft.autoupdate.fba if running..."
killall -9 "com.microsoft.autoupdate.fba" 2>/dev/null || true

# Kill application with bundle ID com.microsoft.autoupdate2 if running
echo "Stopping application with bundle ID com.microsoft.autoupdate2 if running..."
killall -9 "com.microsoft.autoupdate2" 2>/dev/null || true

# Kill application with bundle ID com.microsoft.errorreporting if running
echo "Stopping application with bundle ID com.microsoft.errorreporting if running..."
killall -9 "com.microsoft.errorreporting" 2>/dev/null || true

# Remove $HOME/Library/Application Support/Microsoft AutoUpdate
echo "Removing $HOME/Library/Application Support/Microsoft AutoUpdate..."
if [ -d "$HOME/Library/Application Support/Microsoft AutoUpdate" ]; then
    rm -rf "$HOME/Library/Application Support/Microsoft AutoUpdate" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/Microsoft AutoUpdate" ]; then
    rm -f "$HOME/Library/Application Support/Microsoft AutoUpdate" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.microsoft.autoupdate.fba
echo "Removing $HOME/Library/Caches/com.microsoft.autoupdate.fba..."
if [ -d "$HOME/Library/Caches/com.microsoft.autoupdate.fba" ]; then
    rm -rf "$HOME/Library/Caches/com.microsoft.autoupdate.fba" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.microsoft.autoupdate.fba" ]; then
    rm -f "$HOME/Library/Caches/com.microsoft.autoupdate.fba" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.microsoft.autoupdate2
echo "Removing $HOME/Library/Caches/com.microsoft.autoupdate2..."
if [ -d "$HOME/Library/Caches/com.microsoft.autoupdate2" ]; then
    rm -rf "$HOME/Library/Caches/com.microsoft.autoupdate2" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.microsoft.autoupdate2" ]; then
    rm -f "$HOME/Library/Caches/com.microsoft.autoupdate2" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/Microsoft/uls/com.microsoft.autoupdate.fba
echo "Removing $HOME/Library/Caches/Microsoft/uls/com.microsoft.autoupdate.fba..."
if [ -d "$HOME/Library/Caches/Microsoft/uls/com.microsoft.autoupdate.fba" ]; then
    rm -rf "$HOME/Library/Caches/Microsoft/uls/com.microsoft.autoupdate.fba" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/Microsoft/uls/com.microsoft.autoupdate.fba" ]; then
    rm -f "$HOME/Library/Caches/Microsoft/uls/com.microsoft.autoupdate.fba" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/Microsoft/uls/com.microsoft.autoupdate2
echo "Removing $HOME/Library/Caches/Microsoft/uls/com.microsoft.autoupdate2..."
if [ -d "$HOME/Library/Caches/Microsoft/uls/com.microsoft.autoupdate2" ]; then
    rm -rf "$HOME/Library/Caches/Microsoft/uls/com.microsoft.autoupdate2" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/Microsoft/uls/com.microsoft.autoupdate2" ]; then
    rm -f "$HOME/Library/Caches/Microsoft/uls/com.microsoft.autoupdate2" 2>/dev/null || true
fi

# Remove $HOME/Library/Cookies/com.microsoft.autoupdate.fba.binarycookies
echo "Removing $HOME/Library/Cookies/com.microsoft.autoupdate.fba.binarycookies..."
if [ -d "$HOME/Library/Cookies/com.microsoft.autoupdate.fba.binarycookies" ]; then
    rm -rf "$HOME/Library/Cookies/com.microsoft.autoupdate.fba.binarycookies" 2>/dev/null || true
elif [ -f "$HOME/Library/Cookies/com.microsoft.autoupdate.fba.binarycookies" ]; then
    rm -f "$HOME/Library/Cookies/com.microsoft.autoupdate.fba.binarycookies" 2>/dev/null || true
fi

# Remove $HOME/Library/Cookies/com.microsoft.autoupdate2.binarycookies
echo "Removing $HOME/Library/Cookies/com.microsoft.autoupdate2.binarycookies..."
if [ -d "$HOME/Library/Cookies/com.microsoft.autoupdate2.binarycookies" ]; then
    rm -rf "$HOME/Library/Cookies/com.microsoft.autoupdate2.binarycookies" 2>/dev/null || true
elif [ -f "$HOME/Library/Cookies/com.microsoft.autoupdate2.binarycookies" ]; then
    rm -f "$HOME/Library/Cookies/com.microsoft.autoupdate2.binarycookies" 2>/dev/null || true
fi

# Remove $HOME/Library/HTTPStorages/com.microsoft.autoupdate.fba
echo "Removing $HOME/Library/HTTPStorages/com.microsoft.autoupdate.fba..."
if [ -d "$HOME/Library/HTTPStorages/com.microsoft.autoupdate.fba" ]; then
    rm -rf "$HOME/Library/HTTPStorages/com.microsoft.autoupdate.fba" 2>/dev/null || true
elif [ -f "$HOME/Library/HTTPStorages/com.microsoft.autoupdate.fba" ]; then
    rm -f "$HOME/Library/HTTPStorages/com.microsoft.autoupdate.fba" 2>/dev/null || true
fi

# Remove $HOME/Library/HTTPStorages/com.microsoft.autoupdate2
echo "Removing $HOME/Library/HTTPStorages/com.microsoft.autoupdate2..."
if [ -d "$HOME/Library/HTTPStorages/com.microsoft.autoupdate2" ]; then
    rm -rf "$HOME/Library/HTTPStorages/com.microsoft.autoupdate2" 2>/dev/null || true
elif [ -f "$HOME/Library/HTTPStorages/com.microsoft.autoupdate2" ]; then
    rm -f "$HOME/Library/HTTPStorages/com.microsoft.autoupdate2" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.microsoft.autoupdate.fba.plist
echo "Removing $HOME/Library/Preferences/com.microsoft.autoupdate.fba.plist..."
if [ -d "$HOME/Library/Preferences/com.microsoft.autoupdate.fba.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.microsoft.autoupdate.fba.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.microsoft.autoupdate.fba.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.microsoft.autoupdate.fba.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.microsoft.autoupdate2.plist
echo "Removing $HOME/Library/Preferences/com.microsoft.autoupdate2.plist..."
if [ -d "$HOME/Library/Preferences/com.microsoft.autoupdate2.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.microsoft.autoupdate2.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.microsoft.autoupdate2.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.microsoft.autoupdate2.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/com.microsoft.autoupdate2.savedState
echo "Removing $HOME/Library/Saved Application State/com.microsoft.autoupdate2.savedState..."
if [ -d "$HOME/Library/Saved Application State/com.microsoft.autoupdate2.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/com.microsoft.autoupdate2.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/com.microsoft.autoupdate2.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/com.microsoft.autoupdate2.savedState" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/Microsoft
echo "Removing $HOME/Library/Caches/Microsoft..."
if [ -d "$HOME/Library/Caches/Microsoft" ]; then
    rm -rf "$HOME/Library/Caches/Microsoft" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/Microsoft" ]; then
    rm -f "$HOME/Library/Caches/Microsoft" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/Microsoft/uls
echo "Removing $HOME/Library/Caches/Microsoft/uls..."
if [ -d "$HOME/Library/Caches/Microsoft/uls" ]; then
    rm -rf "$HOME/Library/Caches/Microsoft/uls" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/Microsoft/uls" ]; then
    rm -f "$HOME/Library/Caches/Microsoft/uls" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
