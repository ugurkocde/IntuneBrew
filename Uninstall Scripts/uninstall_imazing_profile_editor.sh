#!/bin/bash
# Uninstall script for iMazing Profile Editor
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling iMazing Profile Editor..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping iMazing Profile Editor if running..."
pkill -f "iMazing Profile Editor" 2>/dev/null || true

# Kill application with bundle ID com.DigiDNA.iMazingProfileEditorMac if running
echo "Stopping application with bundle ID com.DigiDNA.iMazingProfileEditorMac if running..."
killall -9 "com.DigiDNA.iMazingProfileEditorMac" 2>/dev/null || true

# Remove /Applications/iMazing Profile Editor.app
echo "Removing /Applications/iMazing Profile Editor.app..."
if [ -d "/Applications/iMazing Profile Editor.app" ]; then
    rm -rf "/Applications/iMazing Profile Editor.app" 2>/dev/null || true
elif [ -f "/Applications/iMazing Profile Editor.app" ]; then
    rm -f "/Applications/iMazing Profile Editor.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Scripts/com.DigiDNA.iMazingProfileEditorMac
echo "Removing $HOME/Library/Application Scripts/com.DigiDNA.iMazingProfileEditorMac..."
if [ -d "$HOME/Library/Application Scripts/com.DigiDNA.iMazingProfileEditorMac" ]; then
    rm -rf "$HOME/Library/Application Scripts/com.DigiDNA.iMazingProfileEditorMac" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Scripts/com.DigiDNA.iMazingProfileEditorMac" ]; then
    rm -f "$HOME/Library/Application Scripts/com.DigiDNA.iMazingProfileEditorMac" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.plausiblelabs.crashreporter.data/com.DigiDNA.iMazingProfileEditorMac.Mini
echo "Removing $HOME/Library/Caches/com.plausiblelabs.crashreporter.data/com.DigiDNA.iMazingProfileEditorMac.Mini..."
if [ -d "$HOME/Library/Caches/com.plausiblelabs.crashreporter.data/com.DigiDNA.iMazingProfileEditorMac.Mini" ]; then
    rm -rf "$HOME/Library/Caches/com.plausiblelabs.crashreporter.data/com.DigiDNA.iMazingProfileEditorMac.Mini" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.plausiblelabs.crashreporter.data/com.DigiDNA.iMazingProfileEditorMac.Mini" ]; then
    rm -f "$HOME/Library/Caches/com.plausiblelabs.crashreporter.data/com.DigiDNA.iMazingProfileEditorMac.Mini" 2>/dev/null || true
fi

# Remove $HOME/Library/Containers/com.DigiDNA.iMazingProfileEditorMac
echo "Removing $HOME/Library/Containers/com.DigiDNA.iMazingProfileEditorMac..."
if [ -d "$HOME/Library/Containers/com.DigiDNA.iMazingProfileEditorMac" ]; then
    rm -rf "$HOME/Library/Containers/com.DigiDNA.iMazingProfileEditorMac" 2>/dev/null || true
elif [ -f "$HOME/Library/Containers/com.DigiDNA.iMazingProfileEditorMac" ]; then
    rm -f "$HOME/Library/Containers/com.DigiDNA.iMazingProfileEditorMac" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/com.DigiDNA.iMazingProfileEditorMac.savedState
echo "Removing $HOME/Library/Saved Application State/com.DigiDNA.iMazingProfileEditorMac.savedState..."
if [ -d "$HOME/Library/Saved Application State/com.DigiDNA.iMazingProfileEditorMac.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/com.DigiDNA.iMazingProfileEditorMac.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/com.DigiDNA.iMazingProfileEditorMac.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/com.DigiDNA.iMazingProfileEditorMac.savedState" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
