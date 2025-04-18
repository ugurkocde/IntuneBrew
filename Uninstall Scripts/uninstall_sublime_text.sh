#!/bin/bash
# Uninstall script for Sublime Text
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Sublime Text..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Sublime Text if running..."
pkill -f "Sublime Text" 2>/dev/null || true

# Kill application with bundle ID com.sublimetext.4 if running
echo "Stopping application with bundle ID com.sublimetext.4 if running..."
killall -9 "com.sublimetext.4" 2>/dev/null || true

# Remove /Applications/Sublime Text.app
echo "Removing /Applications/Sublime Text.app..."
if [ -d "/Applications/Sublime Text.app" ]; then
    rm -rf "/Applications/Sublime Text.app" 2>/dev/null || true
elif [ -f "/Applications/Sublime Text.app" ]; then
    rm -f "/Applications/Sublime Text.app" 2>/dev/null || true
fi

# Remove binary /Applications/Sublime Text.app/Sublime Text.app/Contents/SharedSupport/bin/subl
echo "Removing binary /Applications/Sublime Text.app/Sublime Text.app/Contents/SharedSupport/bin/subl..."
if [ -f "/Applications/Sublime Text.app/Sublime Text.app/Contents/SharedSupport/bin/subl" ]; then
    rm -f "/Applications/Sublime Text.app/Sublime Text.app/Contents/SharedSupport/bin/subl" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.sublimetext.4.sfl*
echo "Removing $HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.sublimetext.4.sfl*..."
if [ -d "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.sublimetext.4.sfl*" ]; then
    rm -rf "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.sublimetext.4.sfl*" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.sublimetext.4.sfl*" ]; then
    rm -f "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.sublimetext.4.sfl*" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/Sublime Text (Safe Mode)
echo "Removing $HOME/Library/Application Support/Sublime Text (Safe Mode)..."
if [ -d "$HOME/Library/Application Support/Sublime Text (Safe Mode)" ]; then
    rm -rf "$HOME/Library/Application Support/Sublime Text (Safe Mode)" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/Sublime Text (Safe Mode)" ]; then
    rm -f "$HOME/Library/Application Support/Sublime Text (Safe Mode)" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/Sublime Text 3
echo "Removing $HOME/Library/Application Support/Sublime Text 3..."
if [ -d "$HOME/Library/Application Support/Sublime Text 3" ]; then
    rm -rf "$HOME/Library/Application Support/Sublime Text 3" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/Sublime Text 3" ]; then
    rm -f "$HOME/Library/Application Support/Sublime Text 3" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/Sublime Text
echo "Removing $HOME/Library/Application Support/Sublime Text..."
if [ -d "$HOME/Library/Application Support/Sublime Text" ]; then
    rm -rf "$HOME/Library/Application Support/Sublime Text" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/Sublime Text" ]; then
    rm -f "$HOME/Library/Application Support/Sublime Text" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.sublimetext.4
echo "Removing $HOME/Library/Caches/com.sublimetext.4..."
if [ -d "$HOME/Library/Caches/com.sublimetext.4" ]; then
    rm -rf "$HOME/Library/Caches/com.sublimetext.4" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.sublimetext.4" ]; then
    rm -f "$HOME/Library/Caches/com.sublimetext.4" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.sublimetext.3
echo "Removing $HOME/Library/Caches/com.sublimetext.3..."
if [ -d "$HOME/Library/Caches/com.sublimetext.3" ]; then
    rm -rf "$HOME/Library/Caches/com.sublimetext.3" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.sublimetext.3" ]; then
    rm -f "$HOME/Library/Caches/com.sublimetext.3" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/Sublime Text (Safe Mode)
echo "Removing $HOME/Library/Caches/Sublime Text (Safe Mode)..."
if [ -d "$HOME/Library/Caches/Sublime Text (Safe Mode)" ]; then
    rm -rf "$HOME/Library/Caches/Sublime Text (Safe Mode)" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/Sublime Text (Safe Mode)" ]; then
    rm -f "$HOME/Library/Caches/Sublime Text (Safe Mode)" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/Sublime Text 3
echo "Removing $HOME/Library/Caches/Sublime Text 3..."
if [ -d "$HOME/Library/Caches/Sublime Text 3" ]; then
    rm -rf "$HOME/Library/Caches/Sublime Text 3" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/Sublime Text 3" ]; then
    rm -f "$HOME/Library/Caches/Sublime Text 3" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/Sublime Text
echo "Removing $HOME/Library/Caches/Sublime Text..."
if [ -d "$HOME/Library/Caches/Sublime Text" ]; then
    rm -rf "$HOME/Library/Caches/Sublime Text" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/Sublime Text" ]; then
    rm -f "$HOME/Library/Caches/Sublime Text" 2>/dev/null || true
fi

# Remove $HOME/Library/HTTPStorages/com.sublimetext.4
echo "Removing $HOME/Library/HTTPStorages/com.sublimetext.4..."
if [ -d "$HOME/Library/HTTPStorages/com.sublimetext.4" ]; then
    rm -rf "$HOME/Library/HTTPStorages/com.sublimetext.4" 2>/dev/null || true
elif [ -f "$HOME/Library/HTTPStorages/com.sublimetext.4" ]; then
    rm -f "$HOME/Library/HTTPStorages/com.sublimetext.4" 2>/dev/null || true
fi

# Remove $HOME/Library/HTTPStorages/com.sublimetext.3
echo "Removing $HOME/Library/HTTPStorages/com.sublimetext.3..."
if [ -d "$HOME/Library/HTTPStorages/com.sublimetext.3" ]; then
    rm -rf "$HOME/Library/HTTPStorages/com.sublimetext.3" 2>/dev/null || true
elif [ -f "$HOME/Library/HTTPStorages/com.sublimetext.3" ]; then
    rm -f "$HOME/Library/HTTPStorages/com.sublimetext.3" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.sublimetext.4.plist
echo "Removing $HOME/Library/Preferences/com.sublimetext.4.plist..."
if [ -d "$HOME/Library/Preferences/com.sublimetext.4.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.sublimetext.4.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.sublimetext.4.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.sublimetext.4.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.sublimetext.3.plist
echo "Removing $HOME/Library/Preferences/com.sublimetext.3.plist..."
if [ -d "$HOME/Library/Preferences/com.sublimetext.3.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.sublimetext.3.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.sublimetext.3.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.sublimetext.3.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/com.sublimetext.4.savedState
echo "Removing $HOME/Library/Saved Application State/com.sublimetext.4.savedState..."
if [ -d "$HOME/Library/Saved Application State/com.sublimetext.4.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/com.sublimetext.4.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/com.sublimetext.4.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/com.sublimetext.4.savedState" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/com.sublimetext.3.savedState
echo "Removing $HOME/Library/Saved Application State/com.sublimetext.3.savedState..."
if [ -d "$HOME/Library/Saved Application State/com.sublimetext.3.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/com.sublimetext.3.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/com.sublimetext.3.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/com.sublimetext.3.savedState" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
