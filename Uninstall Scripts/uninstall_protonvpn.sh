#!/bin/bash
# Uninstall script for ProtonVPN
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling ProtonVPN..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping ProtonVPN if running..."
pkill -f "ProtonVPN" 2>/dev/null || true

# Unload service ch.protonvpn.ProtonVPNStarter
echo "Unloading service ch.protonvpn.ProtonVPNStarter..."
launchctl unload -w /Library/LaunchAgents/ch.protonvpn.ProtonVPNStarter.plist 2>/dev/null || true
launchctl unload -w /Library/LaunchDaemons/ch.protonvpn.ProtonVPNStarter.plist 2>/dev/null || true
launchctl unload -w ~/Library/LaunchAgents/ch.protonvpn.ProtonVPNStarter.plist 2>/dev/null || true

# Kill application with bundle ID ch.protonvpn.mac if running
echo "Stopping application with bundle ID ch.protonvpn.mac if running..."
killall -9 "ch.protonvpn.mac" 2>/dev/null || true

# Remove /Applications/ProtonVPN.app
echo "Removing /Applications/ProtonVPN.app..."
if [ -d "/Applications/ProtonVPN.app" ]; then
    rm -rf "/Applications/ProtonVPN.app" 2>/dev/null || true
elif [ -f "/Applications/ProtonVPN.app" ]; then
    rm -f "/Applications/ProtonVPN.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Scripts/*.group.ch.protonvpn.mac
echo "Removing $HOME/Library/Application Scripts/*.group.ch.protonvpn.mac..."
if [ -d "$HOME/Library/Application Scripts/*.group.ch.protonvpn.mac" ]; then
    rm -rf "$HOME/Library/Application Scripts/*.group.ch.protonvpn.mac" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Scripts/*.group.ch.protonvpn.mac" ]; then
    rm -f "$HOME/Library/Application Scripts/*.group.ch.protonvpn.mac" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Scripts/ch.protonvpn.*
echo "Removing $HOME/Library/Application Scripts/ch.protonvpn.*..."
if [ -d "$HOME/Library/Application Scripts/ch.protonvpn.*" ]; then
    rm -rf "$HOME/Library/Application Scripts/ch.protonvpn.*" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Scripts/ch.protonvpn.*" ]; then
    rm -f "$HOME/Library/Application Scripts/ch.protonvpn.*" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/CrashReporter/ProtonVPN*
echo "Removing $HOME/Library/Application Support/CrashReporter/ProtonVPN*..."
if [ -d "$HOME/Library/Application Support/CrashReporter/ProtonVPN*" ]; then
    rm -rf "$HOME/Library/Application Support/CrashReporter/ProtonVPN*" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/CrashReporter/ProtonVPN*" ]; then
    rm -f "$HOME/Library/Application Support/CrashReporter/ProtonVPN*" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/ProtonVPN
echo "Removing $HOME/Library/Application Support/ProtonVPN..."
if [ -d "$HOME/Library/Application Support/ProtonVPN" ]; then
    rm -rf "$HOME/Library/Application Support/ProtonVPN" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/ProtonVPN" ]; then
    rm -f "$HOME/Library/Application Support/ProtonVPN" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/ch.protonvpn.mac
echo "Removing $HOME/Library/Caches/ch.protonvpn.mac..."
if [ -d "$HOME/Library/Caches/ch.protonvpn.mac" ]; then
    rm -rf "$HOME/Library/Caches/ch.protonvpn.mac" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/ch.protonvpn.mac" ]; then
    rm -f "$HOME/Library/Caches/ch.protonvpn.mac" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.apple.nsurlsessiond/Downloads/ch.protonvpn.mac
echo "Removing $HOME/Library/Caches/com.apple.nsurlsessiond/Downloads/ch.protonvpn.mac..."
if [ -d "$HOME/Library/Caches/com.apple.nsurlsessiond/Downloads/ch.protonvpn.mac" ]; then
    rm -rf "$HOME/Library/Caches/com.apple.nsurlsessiond/Downloads/ch.protonvpn.mac" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.apple.nsurlsessiond/Downloads/ch.protonvpn.mac" ]; then
    rm -f "$HOME/Library/Caches/com.apple.nsurlsessiond/Downloads/ch.protonvpn.mac" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/SentryCrash/ProtonVPN
echo "Removing $HOME/Library/Caches/SentryCrash/ProtonVPN..."
if [ -d "$HOME/Library/Caches/SentryCrash/ProtonVPN" ]; then
    rm -rf "$HOME/Library/Caches/SentryCrash/ProtonVPN" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/SentryCrash/ProtonVPN" ]; then
    rm -f "$HOME/Library/Caches/SentryCrash/ProtonVPN" 2>/dev/null || true
fi

# Remove $HOME/Library/Containers/ch.protonvpn.*
echo "Removing $HOME/Library/Containers/ch.protonvpn.*..."
if [ -d "$HOME/Library/Containers/ch.protonvpn.*" ]; then
    rm -rf "$HOME/Library/Containers/ch.protonvpn.*" 2>/dev/null || true
elif [ -f "$HOME/Library/Containers/ch.protonvpn.*" ]; then
    rm -f "$HOME/Library/Containers/ch.protonvpn.*" 2>/dev/null || true
fi

# Remove $HOME/Library/Cookies/ch.protonvpn.mac.binarycookies
echo "Removing $HOME/Library/Cookies/ch.protonvpn.mac.binarycookies..."
if [ -d "$HOME/Library/Cookies/ch.protonvpn.mac.binarycookies" ]; then
    rm -rf "$HOME/Library/Cookies/ch.protonvpn.mac.binarycookies" 2>/dev/null || true
elif [ -f "$HOME/Library/Cookies/ch.protonvpn.mac.binarycookies" ]; then
    rm -f "$HOME/Library/Cookies/ch.protonvpn.mac.binarycookies" 2>/dev/null || true
fi

# Remove $HOME/Library/Group Containers/*.group.ch.protonvpn.mac
echo "Removing $HOME/Library/Group Containers/*.group.ch.protonvpn.mac..."
if [ -d "$HOME/Library/Group Containers/*.group.ch.protonvpn.mac" ]; then
    rm -rf "$HOME/Library/Group Containers/*.group.ch.protonvpn.mac" 2>/dev/null || true
elif [ -f "$HOME/Library/Group Containers/*.group.ch.protonvpn.mac" ]; then
    rm -f "$HOME/Library/Group Containers/*.group.ch.protonvpn.mac" 2>/dev/null || true
fi

# Remove $HOME/Library/Logs/ProtonVPN.log
echo "Removing $HOME/Library/Logs/ProtonVPN.log..."
if [ -d "$HOME/Library/Logs/ProtonVPN.log" ]; then
    rm -rf "$HOME/Library/Logs/ProtonVPN.log" 2>/dev/null || true
elif [ -f "$HOME/Library/Logs/ProtonVPN.log" ]; then
    rm -f "$HOME/Library/Logs/ProtonVPN.log" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/ch.protonvpn.mac.plist
echo "Removing $HOME/Library/Preferences/ch.protonvpn.mac.plist..."
if [ -d "$HOME/Library/Preferences/ch.protonvpn.mac.plist" ]; then
    rm -rf "$HOME/Library/Preferences/ch.protonvpn.mac.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/ch.protonvpn.mac.plist" ]; then
    rm -f "$HOME/Library/Preferences/ch.protonvpn.mac.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/WebKit/ch.protonvpn.mac
echo "Removing $HOME/Library/WebKit/ch.protonvpn.mac..."
if [ -d "$HOME/Library/WebKit/ch.protonvpn.mac" ]; then
    rm -rf "$HOME/Library/WebKit/ch.protonvpn.mac" 2>/dev/null || true
elif [ -f "$HOME/Library/WebKit/ch.protonvpn.mac" ]; then
    rm -f "$HOME/Library/WebKit/ch.protonvpn.mac" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
