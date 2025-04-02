#!/bin/bash
# Uninstall script for KeePassXC
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling KeePassXC..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping KeePassXC if running..."
pkill -f "KeePassXC" 2>/dev/null || true

# Kill application with bundle ID org.keepassxc.keepassxc if running
echo "Stopping application with bundle ID org.keepassxc.keepassxc if running..."
killall -9 "org.keepassxc.keepassxc" 2>/dev/null || true

# Remove /Applications/KeePassXC.app
echo "Removing /Applications/KeePassXC.app..."
if [ -d "/Applications/KeePassXC.app" ]; then
    rm -rf "/Applications/KeePassXC.app" 2>/dev/null || true
elif [ -f "/Applications/KeePassXC.app" ]; then
    rm -f "/Applications/KeePassXC.app" 2>/dev/null || true
fi

# Remove binary /Applications/KeePassXC.app/KeePassXC.app/Contents/MacOS/keepassxc-cli
echo "Removing binary /Applications/KeePassXC.app/KeePassXC.app/Contents/MacOS/keepassxc-cli..."
if [ -f "/Applications/KeePassXC.app/KeePassXC.app/Contents/MacOS/keepassxc-cli" ]; then
    rm -f "/Applications/KeePassXC.app/KeePassXC.app/Contents/MacOS/keepassxc-cli" 2>/dev/null || true
fi

# Remove $HOME/.keepassxc
echo "Removing $HOME/.keepassxc..."
if [ -d "$HOME/.keepassxc" ]; then
    rm -rf "$HOME/.keepassxc" 2>/dev/null || true
elif [ -f "$HOME/.keepassxc" ]; then
    rm -f "$HOME/.keepassxc" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/CrashReporter/KeePassXC_*.plist
echo "Removing $HOME/Library/Application Support/CrashReporter/KeePassXC_*.plist..."
if [ -d "$HOME/Library/Application Support/CrashReporter/KeePassXC_*.plist" ]; then
    rm -rf "$HOME/Library/Application Support/CrashReporter/KeePassXC_*.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/CrashReporter/KeePassXC_*.plist" ]; then
    rm -f "$HOME/Library/Application Support/CrashReporter/KeePassXC_*.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/keepassxc
echo "Removing $HOME/Library/Application Support/keepassxc..."
if [ -d "$HOME/Library/Application Support/keepassxc" ]; then
    rm -rf "$HOME/Library/Application Support/keepassxc" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/keepassxc" ]; then
    rm -f "$HOME/Library/Application Support/keepassxc" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/org.keepassx.keepassxc
echo "Removing $HOME/Library/Caches/org.keepassx.keepassxc..."
if [ -d "$HOME/Library/Caches/org.keepassx.keepassxc" ]; then
    rm -rf "$HOME/Library/Caches/org.keepassx.keepassxc" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/org.keepassx.keepassxc" ]; then
    rm -f "$HOME/Library/Caches/org.keepassx.keepassxc" 2>/dev/null || true
fi

# Remove $HOME/Library/Logs/DiagnosticReports/KeePassXC_*.crash
echo "Removing $HOME/Library/Logs/DiagnosticReports/KeePassXC_*.crash..."
if [ -d "$HOME/Library/Logs/DiagnosticReports/KeePassXC_*.crash" ]; then
    rm -rf "$HOME/Library/Logs/DiagnosticReports/KeePassXC_*.crash" 2>/dev/null || true
elif [ -f "$HOME/Library/Logs/DiagnosticReports/KeePassXC_*.crash" ]; then
    rm -f "$HOME/Library/Logs/DiagnosticReports/KeePassXC_*.crash" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/keepassxc.keepassxc.plist
echo "Removing $HOME/Library/Preferences/keepassxc.keepassxc.plist..."
if [ -d "$HOME/Library/Preferences/keepassxc.keepassxc.plist" ]; then
    rm -rf "$HOME/Library/Preferences/keepassxc.keepassxc.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/keepassxc.keepassxc.plist" ]; then
    rm -f "$HOME/Library/Preferences/keepassxc.keepassxc.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/org.keepassx.keepassxc.plist
echo "Removing $HOME/Library/Preferences/org.keepassx.keepassxc.plist..."
if [ -d "$HOME/Library/Preferences/org.keepassx.keepassxc.plist" ]; then
    rm -rf "$HOME/Library/Preferences/org.keepassx.keepassxc.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/org.keepassx.keepassxc.plist" ]; then
    rm -f "$HOME/Library/Preferences/org.keepassx.keepassxc.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/org.keepassx.keepassxc.savedState
echo "Removing $HOME/Library/Saved Application State/org.keepassx.keepassxc.savedState..."
if [ -d "$HOME/Library/Saved Application State/org.keepassx.keepassxc.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/org.keepassx.keepassxc.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/org.keepassx.keepassxc.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/org.keepassx.keepassxc.savedState" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
