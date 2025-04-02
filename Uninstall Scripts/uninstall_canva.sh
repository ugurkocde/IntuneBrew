#!/bin/bash
# Uninstall script for Canva
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Canva..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Canva if running..."
pkill -f "Canva" 2>/dev/null || true

# Remove /Applications/Canva.app
echo "Removing /Applications/Canva.app..."
if [ -d "/Applications/Canva.app" ]; then
    rm -rf "/Applications/Canva.app" 2>/dev/null || true
elif [ -f "/Applications/Canva.app" ]; then
    rm -f "/Applications/Canva.app" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/Canva
echo "Removing $HOME/Library/Application Support/Canva..."
if [ -d "$HOME/Library/Application Support/Canva" ]; then
    rm -rf "$HOME/Library/Application Support/Canva" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/Canva" ]; then
    rm -f "$HOME/Library/Application Support/Canva" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.canva.CanvaDesktop
echo "Removing $HOME/Library/Caches/com.canva.CanvaDesktop..."
if [ -d "$HOME/Library/Caches/com.canva.CanvaDesktop" ]; then
    rm -rf "$HOME/Library/Caches/com.canva.CanvaDesktop" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.canva.CanvaDesktop" ]; then
    rm -f "$HOME/Library/Caches/com.canva.CanvaDesktop" 2>/dev/null || true
fi

# Remove $HOME/Library/Caches/com.canva.CanvaDesktop.ShipIt
echo "Removing $HOME/Library/Caches/com.canva.CanvaDesktop.ShipIt..."
if [ -d "$HOME/Library/Caches/com.canva.CanvaDesktop.ShipIt" ]; then
    rm -rf "$HOME/Library/Caches/com.canva.CanvaDesktop.ShipIt" 2>/dev/null || true
elif [ -f "$HOME/Library/Caches/com.canva.CanvaDesktop.ShipIt" ]; then
    rm -f "$HOME/Library/Caches/com.canva.CanvaDesktop.ShipIt" 2>/dev/null || true
fi

# Remove $HOME/Library/LaunchAgents/com.canva.availability-check-agent.plist
echo "Removing $HOME/Library/LaunchAgents/com.canva.availability-check-agent.plist..."
if [ -d "$HOME/Library/LaunchAgents/com.canva.availability-check-agent.plist" ]; then
    rm -rf "$HOME/Library/LaunchAgents/com.canva.availability-check-agent.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/LaunchAgents/com.canva.availability-check-agent.plist" ]; then
    rm -f "$HOME/Library/LaunchAgents/com.canva.availability-check-agent.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Logs/Canva
echo "Removing $HOME/Library/Logs/Canva..."
if [ -d "$HOME/Library/Logs/Canva" ]; then
    rm -rf "$HOME/Library/Logs/Canva" 2>/dev/null || true
elif [ -f "$HOME/Library/Logs/Canva" ]; then
    rm -f "$HOME/Library/Logs/Canva" 2>/dev/null || true
fi

# Remove $HOME/Library/Preferences/com.canva.CanvaDesktop.plist
echo "Removing $HOME/Library/Preferences/com.canva.CanvaDesktop.plist..."
if [ -d "$HOME/Library/Preferences/com.canva.CanvaDesktop.plist" ]; then
    rm -rf "$HOME/Library/Preferences/com.canva.CanvaDesktop.plist" 2>/dev/null || true
elif [ -f "$HOME/Library/Preferences/com.canva.CanvaDesktop.plist" ]; then
    rm -f "$HOME/Library/Preferences/com.canva.CanvaDesktop.plist" 2>/dev/null || true
fi

# Remove $HOME/Library/Saved Application State/com.canva.CanvaDesktop.savedState
echo "Removing $HOME/Library/Saved Application State/com.canva.CanvaDesktop.savedState..."
if [ -d "$HOME/Library/Saved Application State/com.canva.CanvaDesktop.savedState" ]; then
    rm -rf "$HOME/Library/Saved Application State/com.canva.CanvaDesktop.savedState" 2>/dev/null || true
elif [ -f "$HOME/Library/Saved Application State/com.canva.CanvaDesktop.savedState" ]; then
    rm -f "$HOME/Library/Saved Application State/com.canva.CanvaDesktop.savedState" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
