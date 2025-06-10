#!/bin/bash

# Uninstall script for Starface

# Define the app name and bundle ID
APP_NAME="STARFACE.app"
BUNDLE_ID="de.starface.STARFACE"

echo "Starting uninstallation of Starface..."

# Kill the app if it's running
echo "Terminating Starface processes..."
pkill -f "STARFACE" 2>/dev/null
killall "STARFACE" 2>/dev/null

# Remove the app from Applications folder
if [ -d "/Applications/$APP_NAME" ]; then
    echo "Removing $APP_NAME from Applications folder..."
    rm -rf "/Applications/$APP_NAME"
fi

# Remove app support files
echo "Removing Starface support files..."
rm -rf ~/Library/Application\ Support/STARFACE 2>/dev/null
rm -rf ~/Library/Application\ Support/de.starface.* 2>/dev/null

# Remove preferences
echo "Removing Starface preferences..."
rm -rf ~/Library/Preferences/de.starface.* 2>/dev/null
rm -rf ~/Library/Preferences/com.starface.* 2>/dev/null

# Remove caches
echo "Removing Starface caches..."
rm -rf ~/Library/Caches/de.starface.* 2>/dev/null
rm -rf ~/Library/Caches/com.starface.* 2>/dev/null

# Remove logs
echo "Removing Starface logs..."
rm -rf ~/Library/Logs/STARFACE 2>/dev/null
rm -rf ~/Library/Logs/de.starface.* 2>/dev/null

# Remove saved application state
echo "Removing saved application state..."
rm -rf ~/Library/Saved\ Application\ State/de.starface.* 2>/dev/null

# Remove any LaunchAgents
echo "Removing LaunchAgents..."
rm -f ~/Library/LaunchAgents/de.starface.* 2>/dev/null
rm -f ~/Library/LaunchAgents/com.starface.* 2>/dev/null

# Remove from dock if present
echo "Removing from Dock if present..."
defaults delete com.apple.dock persistent-apps | grep -v "$BUNDLE_ID" | defaults write com.apple.dock persistent-apps
killall Dock 2>/dev/null

echo "Starface uninstallation completed."