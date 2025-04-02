#!/bin/bash
# Uninstall script for Apparency
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Apparency..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Apparency if running..."
pkill -f "Apparency" 2>/dev/null || true

# Remove /Applications/Apparency.app
echo "Removing /Applications/Apparency.app..."
if [ -d "/Applications/Apparency.app" ]; then
    rm -rf "/Applications/Apparency.app" 2>/dev/null || true
elif [ -f "/Applications/Apparency.app" ]; then
    rm -f "/Applications/Apparency.app" 2>/dev/null || true
fi

# Remove binary /Applications/Apparency.app/Apparency.app/Contents/MacOS/appy
echo "Removing binary /Applications/Apparency.app/Apparency.app/Contents/MacOS/appy..."
if [ -f "/Applications/Apparency.app/Apparency.app/Contents/MacOS/appy" ]; then
    rm -f "/Applications/Apparency.app/Apparency.app/Contents/MacOS/appy" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Scripts/*.com.mothersruin.Apparency.SharedPrefs
echo "Removing $HOME/Library/Application Scripts/*.com.mothersruin.Apparency.SharedPrefs..."
if [ -d "$HOME/Library/Application Scripts/*.com.mothersruin.Apparency.SharedPrefs" ]; then
    rm -rf "$HOME/Library/Application Scripts/*.com.mothersruin.Apparency.SharedPrefs" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Scripts/*.com.mothersruin.Apparency.SharedPrefs" ]; then
    rm -f "$HOME/Library/Application Scripts/*.com.mothersruin.Apparency.SharedPrefs" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Scripts/com.mothersruin.Apparency
echo "Removing $HOME/Library/Application Scripts/com.mothersruin.Apparency..."
if [ -d "$HOME/Library/Application Scripts/com.mothersruin.Apparency" ]; then
    rm -rf "$HOME/Library/Application Scripts/com.mothersruin.Apparency" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Scripts/com.mothersruin.Apparency" ]; then
    rm -f "$HOME/Library/Application Scripts/com.mothersruin.Apparency" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Scripts/com.mothersruin.Apparency.QLPreviewExtension
echo "Removing $HOME/Library/Application Scripts/com.mothersruin.Apparency.QLPreviewExtension..."
if [ -d "$HOME/Library/Application Scripts/com.mothersruin.Apparency.QLPreviewExtension" ]; then
    rm -rf "$HOME/Library/Application Scripts/com.mothersruin.Apparency.QLPreviewExtension" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Scripts/com.mothersruin.Apparency.QLPreviewExtension" ]; then
    rm -f "$HOME/Library/Application Scripts/com.mothersruin.Apparency.QLPreviewExtension" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.mothersruin.apparency.sfl*
echo "Removing $HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.mothersruin.apparency.sfl*..."
if [ -d "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.mothersruin.apparency.sfl*" ]; then
    rm -rf "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.mothersruin.apparency.sfl*" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.mothersruin.apparency.sfl*" ]; then
    rm -f "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.mothersruin.apparency.sfl*" 2>/dev/null || true
fi

# Remove $HOME/Library/Containers/com.mothersruin.Apparency
echo "Removing $HOME/Library/Containers/com.mothersruin.Apparency..."
if [ -d "$HOME/Library/Containers/com.mothersruin.Apparency" ]; then
    rm -rf "$HOME/Library/Containers/com.mothersruin.Apparency" 2>/dev/null || true
elif [ -f "$HOME/Library/Containers/com.mothersruin.Apparency" ]; then
    rm -f "$HOME/Library/Containers/com.mothersruin.Apparency" 2>/dev/null || true
fi

# Remove $HOME/Library/Containers/com.mothersruin.Apparency.QLPreviewExtension
echo "Removing $HOME/Library/Containers/com.mothersruin.Apparency.QLPreviewExtension..."
if [ -d "$HOME/Library/Containers/com.mothersruin.Apparency.QLPreviewExtension" ]; then
    rm -rf "$HOME/Library/Containers/com.mothersruin.Apparency.QLPreviewExtension" 2>/dev/null || true
elif [ -f "$HOME/Library/Containers/com.mothersruin.Apparency.QLPreviewExtension" ]; then
    rm -f "$HOME/Library/Containers/com.mothersruin.Apparency.QLPreviewExtension" 2>/dev/null || true
fi

# Remove $HOME/Library/Group Containers/*.com.mothersruin.Apparency.SharedPrefs
echo "Removing $HOME/Library/Group Containers/*.com.mothersruin.Apparency.SharedPrefs..."
if [ -d "$HOME/Library/Group Containers/*.com.mothersruin.Apparency.SharedPrefs" ]; then
    rm -rf "$HOME/Library/Group Containers/*.com.mothersruin.Apparency.SharedPrefs" 2>/dev/null || true
elif [ -f "$HOME/Library/Group Containers/*.com.mothersruin.Apparency.SharedPrefs" ]; then
    rm -f "$HOME/Library/Group Containers/*.com.mothersruin.Apparency.SharedPrefs" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
