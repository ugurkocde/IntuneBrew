#!/bin/bash
# Uninstall script for Notion
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Notion..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Notion if running..."
pkill -f "Notion" 2>/dev/null || true

# Remove /Applications/Notion.app
echo "Removing /Applications/Notion.app..."
if [ -d "/Applications/Notion.app" ]; then
    rm -rf "/Applications/Notion.app" 2>/dev/null || true
elif [ -f "/Applications/Notion.app" ]; then
    rm -f "/Applications/Notion.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/Caches/notion-updater
echo "Removing $HOME/Library/Application Support/Caches/notion-updater..."
if [ -d "$HOME/Library/Application Support/Caches/notion-updater" ]; then
    rm -rf "$HOME/Library/Application Support/Caches/notion-updater" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/Caches/notion-updater" ]; then
    rm -f "$HOME/Library/Application Support/Caches/notion-updater" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/notion.id.sfl*
echo "Removing $HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/notion.id.sfl*..."
if [ -d "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/notion.id.sfl*" ]; then
    rm -rf "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/notion.id.sfl*" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/notion.id.sfl*" ]; then
    rm -f "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/notion.id.sfl*" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/Notion
echo "Removing $HOME/Library/Application Support/Notion..."
if [ -d "$HOME/Library/Application Support/Notion" ]; then
    rm -rf "$HOME/Library/Application Support/Notion" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/Notion" ]; then
    rm -f "$HOME/Library/Application Support/Notion" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/notion.id*
echo "Removing $HOME/Library/Caches/notion.id*..."
if [ -d "$HOME/Library/Caches/notion.id*" ]; then
    rm -rf "$HOME/Library/Caches/notion.id*" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/notion.id*" ]; then
    rm -f "$HOME/Library/Caches/notion.id*" 2>/dev/null || true
fi

# Remove $HOME/Library/Logs/Notion
echo "Removing $HOME/Library/Logs/Notion..."
if [ -d "$HOME/Library/Logs/Notion" ]; then
    rm -rf "$HOME/Library/Logs/Notion" 2>/dev/null || true
elif [ -f "$HOME/Library/Logs/Notion" ]; then
    rm -f "$HOME/Library/Logs/Notion" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/ByHost/notion.id.*
echo "Removing $HOME/Library/Preferences/ByHost/notion.id.*..."
if [ -d "$HOME/Library/Preferences/ByHost/notion.id.*" ]; then
    rm -rf "$HOME/Library/Preferences/ByHost/notion.id.*" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/ByHost/notion.id.*" ]; then
    rm -f "$HOME/Library/Preferences/ByHost/notion.id.*" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/notion.id.*
echo "Removing $HOME/Library/Preferences/notion.id.*..."
if [ -d "$HOME/Library/Preferences/notion.id.*" ]; then
    rm -rf "$HOME/Library/Preferences/notion.id.*" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/notion.id.*" ]; then
    rm -f "$HOME/Library/Preferences/notion.id.*" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/notion.id.savedState
echo "Removing $HOME/Library/Saved Application State/notion.id.savedState..."
if [ -d "$HOME/Library/Saved Application State/notion.id.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/notion.id.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/notion.id.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/notion.id.savedState" 2>/dev/null || true
fi

# Remove $HOME/Library/WebKit/notion.id
echo "Removing $HOME/Library/WebKit/notion.id..."
if [ -d "$HOME/Library/WebKit/notion.id" ]; then
    rm -rf "$HOME/Library/WebKit/notion.id" 2>/dev/null || true
elif [ -f "$HOME/Library/WebKit/notion.id" ]; then
    rm -f "$HOME/Library/WebKit/notion.id" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
