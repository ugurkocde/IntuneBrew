#!/bin/bash
# Uninstall script for DataGrip
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling DataGrip..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping DataGrip if running..."
pkill -f "DataGrip" 2>/dev/null || true

# Remove /Applications/DataGrip.app
echo "Removing /Applications/DataGrip.app..."
if [ -d "/Applications/DataGrip.app" ]; then
    rm -rf "/Applications/DataGrip.app" 2>/dev/null || true
elif [ -f "/Applications/DataGrip.app" ]; then
    rm -f "/Applications/DataGrip.app" 2>/dev/null || true
fi

# Remove binary /Applications/DataGrip.app/DataGrip.app/Contents/MacOS/datagrip
echo "Removing binary /Applications/DataGrip.app/DataGrip.app/Contents/MacOS/datagrip..."
if [ -f "/Applications/DataGrip.app/DataGrip.app/Contents/MacOS/datagrip" ]; then
    rm -f "/Applications/DataGrip.app/DataGrip.app/Contents/MacOS/datagrip" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/JetBrains/DataGrip*
echo "Removing $HOME/Library/Application Support/JetBrains/DataGrip*..."
if [ -d "$HOME/Library/Application Support/JetBrains/DataGrip*" ]; then
    rm -rf "$HOME/Library/Application Support/JetBrains/DataGrip*" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/JetBrains/DataGrip*" ]; then
    rm -f "$HOME/Library/Application Support/JetBrains/DataGrip*" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/JetBrains/DataGrip*
echo "Removing $HOME/Library/Caches/JetBrains/DataGrip*..."
if [ -d "$HOME/Library/Caches/JetBrains/DataGrip*" ]; then
    rm -rf "$HOME/Library/Caches/JetBrains/DataGrip*" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/JetBrains/DataGrip*" ]; then
    rm -f "$HOME/Library/Caches/JetBrains/DataGrip*" 2>/dev/null || true
fi

# Remove $HOME/Library/Logs/JetBrains/DataGrip*
echo "Removing $HOME/Library/Logs/JetBrains/DataGrip*..."
if [ -d "$HOME/Library/Logs/JetBrains/DataGrip*" ]; then
    rm -rf "$HOME/Library/Logs/JetBrains/DataGrip*" 2>/dev/null || true
elif [ -f "$HOME/Library/Logs/JetBrains/DataGrip*" ]; then
    rm -f "$HOME/Library/Logs/JetBrains/DataGrip*" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/com.jetbrains.datagrip.savedState
echo "Removing $HOME/Library/Saved Application State/com.jetbrains.datagrip.savedState..."
if [ -d "$HOME/Library/Saved Application State/com.jetbrains.datagrip.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/com.jetbrains.datagrip.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/com.jetbrains.datagrip.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/com.jetbrains.datagrip.savedState" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
