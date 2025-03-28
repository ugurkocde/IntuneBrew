#!/bin/bash
# Uninstall script for Gemini
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Gemini..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Gemini if running..."
pkill -f "Gemini" 2>/dev/null || true

# Remove /Applications/Gemini 2.app
echo "Removing /Applications/Gemini 2.app..."
if [ -d "/Applications/Gemini 2.app" ]; then
    rm -rf "/Applications/Gemini 2.app" 2>/dev/null || true
elif [ -f "/Applications/Gemini 2.app" ]; then
    rm -f "/Applications/Gemini 2.app" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
