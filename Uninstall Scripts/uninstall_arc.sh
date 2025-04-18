#!/bin/bash
# Uninstall script for Arc
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Arc..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Arc if running..."
pkill -f "Arc" 2>/dev/null || true

# Kill application with bundle ID company.thebrowser.Browser if running
echo "Stopping application with bundle ID company.thebrowser.Browser if running..."
killall -9 "company.thebrowser.Browser" 2>/dev/null || true

# Remove /Applications/Arc.app
echo "Removing /Applications/Arc.app..."
if [ -d "/Applications/Arc.app" ]; then
    rm -rf "/Applications/Arc.app" 2>/dev/null || true
elif [ -f "/Applications/Arc.app" ]; then
    rm -f "/Applications/Arc.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/Arc
echo "Removing $HOME/Library/Application Support/Arc..."
if [ -d "$HOME/Library/Application Support/Arc" ]; then
    rm -rf "$HOME/Library/Application Support/Arc" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/Arc" ]; then
    rm -f "$HOME/Library/Application Support/Arc" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/Arc
echo "Removing $HOME/Library/Caches/Arc..."
if [ -d "$HOME/Library/Caches/Arc" ]; then
    rm -rf "$HOME/Library/Caches/Arc" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/Arc" ]; then
    rm -f "$HOME/Library/Caches/Arc" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/CloudKit/company.thebrowser.Browser
echo "Removing $HOME/Library/Caches/CloudKit/company.thebrowser.Browser..."
if [ -d "$HOME/Library/Caches/CloudKit/company.thebrowser.Browser" ]; then
    rm -rf "$HOME/Library/Caches/CloudKit/company.thebrowser.Browser" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/CloudKit/company.thebrowser.Browser" ]; then
    rm -f "$HOME/Library/Caches/CloudKit/company.thebrowser.Browser" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/company.thebrowser.Browser
echo "Removing $HOME/Library/Caches/company.thebrowser.Browser..."
if [ -d "$HOME/Library/Caches/company.thebrowser.Browser" ]; then
    rm -rf "$HOME/Library/Caches/company.thebrowser.Browser" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/company.thebrowser.Browser" ]; then
    rm -f "$HOME/Library/Caches/company.thebrowser.Browser" 2>/dev/null || true
fi

# Remove $HOME/Library/HTTPStorages/company.thebrowser.Browser
echo "Removing $HOME/Library/HTTPStorages/company.thebrowser.Browser..."
if [ -d "$HOME/Library/HTTPStorages/company.thebrowser.Browser" ]; then
    rm -rf "$HOME/Library/HTTPStorages/company.thebrowser.Browser" 2>/dev/null || true
elif [ -f "$HOME/Library/HTTPStorages/company.thebrowser.Browser" ]; then
    rm -f "$HOME/Library/HTTPStorages/company.thebrowser.Browser" 2>/dev/null || true
fi

# Remove $HOME/Library/HTTPStorages/company.thebrowser.Browser.binarycookies
echo "Removing $HOME/Library/HTTPStorages/company.thebrowser.Browser.binarycookies..."
if [ -d "$HOME/Library/HTTPStorages/company.thebrowser.Browser.binarycookies" ]; then
    rm -rf "$HOME/Library/HTTPStorages/company.thebrowser.Browser.binarycookies" 2>/dev/null || true
elif [ -f "$HOME/Library/HTTPStorages/company.thebrowser.Browser.binarycookies" ]; then
    rm -f "$HOME/Library/HTTPStorages/company.thebrowser.Browser.binarycookies" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/company.thebrowser.Browser.plist
echo "Removing $HOME/Library/Preferences/company.thebrowser.Browser.plist..."
if [ -d "$HOME/Library/Preferences/company.thebrowser.Browser.plist" ]; then
    rm -rf "$HOME/Library/Preferences/company.thebrowser.Browser.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/company.thebrowser.Browser.plist" ]; then
    rm -f "$HOME/Library/Preferences/company.thebrowser.Browser.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/company.thebrowser.Browser.savedState
echo "Removing $HOME/Library/Saved Application State/company.thebrowser.Browser.savedState..."
if [ -d "$HOME/Library/Saved Application State/company.thebrowser.Browser.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/company.thebrowser.Browser.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/company.thebrowser.Browser.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/company.thebrowser.Browser.savedState" 2>/dev/null || true
fi

# Remove $HOME/Library/WebKit/company.thebrowser.Browser
echo "Removing $HOME/Library/WebKit/company.thebrowser.Browser..."
if [ -d "$HOME/Library/WebKit/company.thebrowser.Browser" ]; then
    rm -rf "$HOME/Library/WebKit/company.thebrowser.Browser" 2>/dev/null || true
elif [ -f "$HOME/Library/WebKit/company.thebrowser.Browser" ]; then
    rm -f "$HOME/Library/WebKit/company.thebrowser.Browser" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
