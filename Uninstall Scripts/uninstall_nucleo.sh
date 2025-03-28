#!/bin/bash
# Uninstall script for Nucleo
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling Nucleo..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping Nucleo if running..."
pkill -f "Nucleo" 2>/dev/null || true

# Remove /Applications/Nucleo.app
echo "Removing /Applications/Nucleo.app..."
if [ -d "/Applications/Nucleo.app" ]; then
    rm -rf "/Applications/Nucleo.app" 2>/dev/null || true
elif [ -f "/Applications/Nucleo.app" ]; then
    rm -f "/Applications/Nucleo.app" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
