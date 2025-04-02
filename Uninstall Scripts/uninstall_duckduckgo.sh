#!/bin/bash
# Uninstall script for DuckDuckGo
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling DuckDuckGo..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping DuckDuckGo if running..."
pkill -f "DuckDuckGo" 2>/dev/null || true

# Remove /Applications/DuckDuckGo.app
echo "Removing /Applications/DuckDuckGo.app..."
if [ -d "/Applications/DuckDuckGo.app" ]; then
    rm -rf "/Applications/DuckDuckGo.app" 2>/dev/null || true
elif [ -f "/Applications/DuckDuckGo.app" ]; then
    rm -f "/Applications/DuckDuckGo.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.duckduckgo.macos.browser
echo "Removing $HOME/Library/Caches/com.duckduckgo.macos.browser..."
if [ -d "$HOME/Library/Caches/com.duckduckgo.macos.browser" ]; then
    rm -rf "$HOME/Library/Caches/com.duckduckgo.macos.browser" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.duckduckgo.macos.browser" ]; then
    rm -f "$HOME/Library/Caches/com.duckduckgo.macos.browser" 2>/dev/null || true
fi

# Remove $HOME/Library/Containers/com.duckduckgo.macos.browser
echo "Removing $HOME/Library/Containers/com.duckduckgo.macos.browser..."
if [ -d "$HOME/Library/Containers/com.duckduckgo.macos.browser" ]; then
    rm -rf "$HOME/Library/Containers/com.duckduckgo.macos.browser" 2>/dev/null || true
elif [ -f "$HOME/Library/Containers/com.duckduckgo.macos.browser" ]; then
    rm -f "$HOME/Library/Containers/com.duckduckgo.macos.browser" 2>/dev/null || true
fi

# Remove $HOME/Library/HTTPStorages/com.duckduckgo.macos.browser
echo "Removing $HOME/Library/HTTPStorages/com.duckduckgo.macos.browser..."
if [ -d "$HOME/Library/HTTPStorages/com.duckduckgo.macos.browser" ]; then
    rm -rf "$HOME/Library/HTTPStorages/com.duckduckgo.macos.browser" 2>/dev/null || true
elif [ -f "$HOME/Library/HTTPStorages/com.duckduckgo.macos.browser" ]; then
    rm -f "$HOME/Library/HTTPStorages/com.duckduckgo.macos.browser" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.duckduckgo.macos.browser.plist
echo "Removing $HOME/Library/Preferences/com.duckduckgo.macos.browser.plist..."
if [ -d "$HOME/Library/Preferences/com.duckduckgo.macos.browser.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.duckduckgo.macos.browser.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.duckduckgo.macos.browser.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.duckduckgo.macos.browser.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/com.duckduckgo.macos.browser.savedState
echo "Removing $HOME/Library/Saved Application State/com.duckduckgo.macos.browser.savedState..."
if [ -d "$HOME/Library/Saved Application State/com.duckduckgo.macos.browser.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/com.duckduckgo.macos.browser.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/com.duckduckgo.macos.browser.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/com.duckduckgo.macos.browser.savedState" 2>/dev/null || true
fi

# Remove $HOME/Library/WebKit/com.duckduckgo.macos.browser
echo "Removing $HOME/Library/WebKit/com.duckduckgo.macos.browser..."
if [ -d "$HOME/Library/WebKit/com.duckduckgo.macos.browser" ]; then
    rm -rf "$HOME/Library/WebKit/com.duckduckgo.macos.browser" 2>/dev/null || true
elif [ -f "$HOME/Library/WebKit/com.duckduckgo.macos.browser" ]; then
    rm -f "$HOME/Library/WebKit/com.duckduckgo.macos.browser" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
