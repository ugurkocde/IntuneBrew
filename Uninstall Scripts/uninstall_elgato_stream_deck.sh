#!/bin/bash
# Uninstall script for Elgato Stream Deck
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Elgato Stream Deck..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Elgato Stream Deck if running..."
pkill -f "Elgato Stream Deck" 2>/dev/null || true

# Unload service com.elgato.StreamDeck
echo "Unloading service com.elgato.StreamDeck..."
launchctl unload -w /Library/LaunchAgents/com.elgato.StreamDeck.plist 2>/dev/null || true
launchctl unload -w /Library/LaunchDaemons/com.elgato.StreamDeck.plist 2>/dev/null || true
launchctl unload -w ~/Library/LaunchAgents/com.elgato.StreamDeck.plist 2>/dev/null || true

# Kill application with bundle ID com.elgato.StreamDeck if running
echo "Stopping application with bundle ID com.elgato.StreamDeck if running..."
killall -9 "com.elgato.StreamDeck" 2>/dev/null || true

# Remove $HOME/Library/Application Support/com.elgato.StreamDeck
echo "Removing $HOME/Library/Application Support/com.elgato.StreamDeck..."
if [ -d "$HOME/Library/Application Support/com.elgato.StreamDeck" ]; then
    rm -rf "$HOME/Library/Application Support/com.elgato.StreamDeck" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/com.elgato.StreamDeck" ]; then
    rm -f "$HOME/Library/Application Support/com.elgato.StreamDeck" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.elgato.StreamDeck
echo "Removing $HOME/Library/Caches/com.elgato.StreamDeck..."
if [ -d "$HOME/Library/Caches/com.elgato.StreamDeck" ]; then
    rm -rf "$HOME/Library/Caches/com.elgato.StreamDeck" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.elgato.StreamDeck" ]; then
    rm -f "$HOME/Library/Caches/com.elgato.StreamDeck" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.plausiblelabs.crashreporter.data/com.elgato.StreamDeck
echo "Removing $HOME/Library/Caches/com.plausiblelabs.crashreporter.data/com.elgato.StreamDeck..."
if [ -d "$HOME/Library/Caches/com.plausiblelabs.crashreporter.data/com.elgato.StreamDeck" ]; then
    rm -rf "$HOME/Library/Caches/com.plausiblelabs.crashreporter.data/com.elgato.StreamDeck" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.plausiblelabs.crashreporter.data/com.elgato.StreamDeck" ]; then
    rm -f "$HOME/Library/Caches/com.plausiblelabs.crashreporter.data/com.elgato.StreamDeck" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.elgato.StreamDeck.plist
echo "Removing $HOME/Library/Preferences/com.elgato.StreamDeck.plist..."
if [ -d "$HOME/Library/Preferences/com.elgato.StreamDeck.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.elgato.StreamDeck.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.elgato.StreamDeck.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.elgato.StreamDeck.plist" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
