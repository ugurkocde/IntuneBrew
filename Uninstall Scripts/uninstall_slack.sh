#!/bin/bash
# Uninstall script for Slack
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Slack..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Slack if running..."
pkill -f "Slack" 2>/dev/null || true

# Kill application with bundle ID com.tinyspeck.slackmacgap if running
echo "Stopping application with bundle ID com.tinyspeck.slackmacgap if running..."
killall -9 "com.tinyspeck.slackmacgap" 2>/dev/null || true

# Remove /Applications/Slack.app
echo "Removing /Applications/Slack.app..."
if [ -d "/Applications/Slack.app" ]; then
    rm -rf "/Applications/Slack.app" 2>/dev/null || true
elif [ -f "/Applications/Slack.app" ]; then
    rm -f "/Applications/Slack.app" 2>/dev/null || true
fi

# Remove /Library/Logs/DiagnosticReports/Slack_*
echo "Removing /Library/Logs/DiagnosticReports/Slack_*..."
if [ -d "/Library/Logs/DiagnosticReports/Slack_*" ]; then
    rm -rf "/Library/Logs/DiagnosticReports/Slack_*" 2>/dev/null || true
elif [ -f "/Library/Logs/DiagnosticReports/Slack_*" ]; then
    rm -f "/Library/Logs/DiagnosticReports/Slack_*" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Scripts/com.tinyspeck.slackmacgap
echo "Removing $HOME/Library/Application Scripts/com.tinyspeck.slackmacgap..."
if [ -d "$HOME/Library/Application Scripts/com.tinyspeck.slackmacgap" ]; then
    rm -rf "$HOME/Library/Application Scripts/com.tinyspeck.slackmacgap" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Scripts/com.tinyspeck.slackmacgap" ]; then
    rm -f "$HOME/Library/Application Scripts/com.tinyspeck.slackmacgap" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.tinyspeck.slackmacgap.sfl*
echo "Removing $HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.tinyspeck.slackmacgap.sfl*..."
if [ -d "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.tinyspeck.slackmacgap.sfl*" ]; then
    rm -rf "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.tinyspeck.slackmacgap.sfl*" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.tinyspeck.slackmacgap.sfl*" ]; then
    rm -f "$HOME/Library/Application Support/com.apple.sharedfilelist/com.apple.LSSharedFileList.ApplicationRecentDocuments/com.tinyspeck.slackmacgap.sfl*" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/Slack
echo "Removing $HOME/Library/Application Support/Slack..."
if [ -d "$HOME/Library/Application Support/Slack" ]; then
    rm -rf "$HOME/Library/Application Support/Slack" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/Slack" ]; then
    rm -f "$HOME/Library/Application Support/Slack" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.tinyspeck.slackmacgap*
echo "Removing $HOME/Library/Caches/com.tinyspeck.slackmacgap*..."
if [ -d "$HOME/Library/Caches/com.tinyspeck.slackmacgap*" ]; then
    rm -rf "$HOME/Library/Caches/com.tinyspeck.slackmacgap*" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.tinyspeck.slackmacgap*" ]; then
    rm -f "$HOME/Library/Caches/com.tinyspeck.slackmacgap*" 2>/dev/null || true
fi

# Remove $HOME/Library/Containers/com.tinyspeck.slackmacgap*
echo "Removing $HOME/Library/Containers/com.tinyspeck.slackmacgap*..."
if [ -d "$HOME/Library/Containers/com.tinyspeck.slackmacgap*" ]; then
    rm -rf "$HOME/Library/Containers/com.tinyspeck.slackmacgap*" 2>/dev/null || true
elif [ -f "$HOME/Library/Containers/com.tinyspeck.slackmacgap*" ]; then
    rm -f "$HOME/Library/Containers/com.tinyspeck.slackmacgap*" 2>/dev/null || true
fi

# Remove $HOME/Library/Cookies/com.tinyspeck.slackmacgap.binarycookies
echo "Removing $HOME/Library/Cookies/com.tinyspeck.slackmacgap.binarycookies..."
if [ -d "$HOME/Library/Cookies/com.tinyspeck.slackmacgap.binarycookies" ]; then
    rm -rf "$HOME/Library/Cookies/com.tinyspeck.slackmacgap.binarycookies" 2>/dev/null || true
elif [ -f "$HOME/Library/Cookies/com.tinyspeck.slackmacgap.binarycookies" ]; then
    rm -f "$HOME/Library/Cookies/com.tinyspeck.slackmacgap.binarycookies" 2>/dev/null || true
fi

# Remove $HOME/Library/Group Containers/*.com.tinyspeck.slackmacgap
echo "Removing $HOME/Library/Group Containers/*.com.tinyspeck.slackmacgap..."
if [ -d "$HOME/Library/Group Containers/*.com.tinyspeck.slackmacgap" ]; then
    rm -rf "$HOME/Library/Group Containers/*.com.tinyspeck.slackmacgap" 2>/dev/null || true
elif [ -f "$HOME/Library/Group Containers/*.com.tinyspeck.slackmacgap" ]; then
    rm -f "$HOME/Library/Group Containers/*.com.tinyspeck.slackmacgap" 2>/dev/null || true
fi

# Remove $HOME/Library/Group Containers/*.slack
echo "Removing $HOME/Library/Group Containers/*.slack..."
if [ -d "$HOME/Library/Group Containers/*.slack" ]; then
    rm -rf "$HOME/Library/Group Containers/*.slack" 2>/dev/null || true
elif [ -f "$HOME/Library/Group Containers/*.slack" ]; then
    rm -f "$HOME/Library/Group Containers/*.slack" 2>/dev/null || true
fi

# Remove $HOME/Library/HTTPStorages/com.tinyspeck.slackmacgap*
echo "Removing $HOME/Library/HTTPStorages/com.tinyspeck.slackmacgap*..."
if [ -d "$HOME/Library/HTTPStorages/com.tinyspeck.slackmacgap*" ]; then
    rm -rf "$HOME/Library/HTTPStorages/com.tinyspeck.slackmacgap*" 2>/dev/null || true
elif [ -f "$HOME/Library/HTTPStorages/com.tinyspeck.slackmacgap*" ]; then
    rm -f "$HOME/Library/HTTPStorages/com.tinyspeck.slackmacgap*" 2>/dev/null || true
fi

# Remove $HOME/Library/Logs/Slack
echo "Removing $HOME/Library/Logs/Slack..."
if [ -d "$HOME/Library/Logs/Slack" ]; then
    rm -rf "$HOME/Library/Logs/Slack" 2>/dev/null || true
elif [ -f "$HOME/Library/Logs/Slack" ]; then
    rm -f "$HOME/Library/Logs/Slack" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/ByHost/com.tinyspeck.slackmacgap.ShipIt.*.plist
echo "Removing $HOME/Library/Preferences/ByHost/com.tinyspeck.slackmacgap.ShipIt.*.plist..."
if [ -d "$HOME/Library/Preferences/ByHost/com.tinyspeck.slackmacgap.ShipIt.*.plist" ]; then
    rm -rf "$HOME/Library/Preferences/ByHost/com.tinyspeck.slackmacgap.ShipIt.*.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/ByHost/com.tinyspeck.slackmacgap.ShipIt.*.plist" ]; then
    rm -f "$HOME/Library/Preferences/ByHost/com.tinyspeck.slackmacgap.ShipIt.*.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.tinyspeck.slackmacgap*
echo "Removing $HOME/Library/Preferences/com.tinyspeck.slackmacgap*..."
if [ -d "$HOME/Library/Preferences/com.tinyspeck.slackmacgap*" ]; then
    rm -rf "$HOME/Library/Preferences/com.tinyspeck.slackmacgap*" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.tinyspeck.slackmacgap*" ]; then
    rm -f "$HOME/Library/Preferences/com.tinyspeck.slackmacgap*" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/com.tinyspeck.slackmacgap.savedState
echo "Removing $HOME/Library/Saved Application State/com.tinyspeck.slackmacgap.savedState..."
if [ -d "$HOME/Library/Saved Application State/com.tinyspeck.slackmacgap.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/com.tinyspeck.slackmacgap.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/com.tinyspeck.slackmacgap.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/com.tinyspeck.slackmacgap.savedState" 2>/dev/null || true
fi

# Remove $HOME/Library/WebKit/com.tinyspeck.slackmacgap
echo "Removing $HOME/Library/WebKit/com.tinyspeck.slackmacgap..."
if [ -d "$HOME/Library/WebKit/com.tinyspeck.slackmacgap" ]; then
    rm -rf "$HOME/Library/WebKit/com.tinyspeck.slackmacgap" 2>/dev/null || true
elif [ -f "$HOME/Library/WebKit/com.tinyspeck.slackmacgap" ]; then
    rm -f "$HOME/Library/WebKit/com.tinyspeck.slackmacgap" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
