#!/bin/bash
# Uninstall script for BusyContacts
# Generated by IntuneBrew

# Exit on error
set -e

echo "Uninstalling BusyContacts..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Kill application process if running
echo "Stopping BusyContacts if running..."
pkill -f "BusyContacts" 2>/dev/null || true

# Kill application with bundle ID com.busymac.busycontacts if running
echo "Stopping application with bundle ID com.busymac.busycontacts if running..."
killall -9 "com.busymac.busycontacts" 2>/dev/null || true

# Remove $HOME/Library/Application Scripts/com.busymac.busycontacts
echo "Removing $HOME/Library/Application Scripts/com.busymac.busycontacts..."
if [ -d "$HOME/Library/Application Scripts/com.busymac.busycontacts" ]; then
    rm -rf "$HOME/Library/Application Scripts/com.busymac.busycontacts" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Scripts/com.busymac.busycontacts" ]; then
    rm -f "$HOME/Library/Application Scripts/com.busymac.busycontacts" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Scripts/N4RA379GBW.com.busymac.busycontacts
echo "Removing $HOME/Library/Application Scripts/N4RA379GBW.com.busymac.busycontacts..."
if [ -d "$HOME/Library/Application Scripts/N4RA379GBW.com.busymac.busycontacts" ]; then
    rm -rf "$HOME/Library/Application Scripts/N4RA379GBW.com.busymac.busycontacts" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Scripts/N4RA379GBW.com.busymac.busycontacts" ]; then
    rm -f "$HOME/Library/Application Scripts/N4RA379GBW.com.busymac.busycontacts" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Scripts/N4RA379GBW.com.busymac.contacts
echo "Removing $HOME/Library/Application Scripts/N4RA379GBW.com.busymac.contacts..."
if [ -d "$HOME/Library/Application Scripts/N4RA379GBW.com.busymac.contacts" ]; then
    rm -rf "$HOME/Library/Application Scripts/N4RA379GBW.com.busymac.contacts" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Scripts/N4RA379GBW.com.busymac.contacts" ]; then
    rm -f "$HOME/Library/Application Scripts/N4RA379GBW.com.busymac.contacts" 2>/dev/null || true
fi

# Remove $HOME/Library/Application Support/Mail/BusyContacts
echo "Removing $HOME/Library/Application Support/Mail/BusyContacts..."
if [ -d "$HOME/Library/Application Support/Mail/BusyContacts" ]; then
    rm -rf "$HOME/Library/Application Support/Mail/BusyContacts" 2>/dev/null || true
elif [ -f "$HOME/Library/Application Support/Mail/BusyContacts" ]; then
    rm -f "$HOME/Library/Application Support/Mail/BusyContacts" 2>/dev/null || true
fi

# Remove $HOME/Library/Containers/com.busymac.busycontacts
echo "Removing $HOME/Library/Containers/com.busymac.busycontacts..."
if [ -d "$HOME/Library/Containers/com.busymac.busycontacts" ]; then
    rm -rf "$HOME/Library/Containers/com.busymac.busycontacts" 2>/dev/null || true
elif [ -f "$HOME/Library/Containers/com.busymac.busycontacts" ]; then
    rm -f "$HOME/Library/Containers/com.busymac.busycontacts" 2>/dev/null || true
fi

# Remove $HOME/Library/Group Containers/N4RA379GBW.com.busymac.busycontacts
echo "Removing $HOME/Library/Group Containers/N4RA379GBW.com.busymac.busycontacts..."
if [ -d "$HOME/Library/Group Containers/N4RA379GBW.com.busymac.busycontacts" ]; then
    rm -rf "$HOME/Library/Group Containers/N4RA379GBW.com.busymac.busycontacts" 2>/dev/null || true
elif [ -f "$HOME/Library/Group Containers/N4RA379GBW.com.busymac.busycontacts" ]; then
    rm -f "$HOME/Library/Group Containers/N4RA379GBW.com.busymac.busycontacts" 2>/dev/null || true
fi

# Remove $HOME/Library/Group Containers/N4RA379GBW.com.busymac.contacts
echo "Removing $HOME/Library/Group Containers/N4RA379GBW.com.busymac.contacts..."
if [ -d "$HOME/Library/Group Containers/N4RA379GBW.com.busymac.contacts" ]; then
    rm -rf "$HOME/Library/Group Containers/N4RA379GBW.com.busymac.contacts" 2>/dev/null || true
elif [ -f "$HOME/Library/Group Containers/N4RA379GBW.com.busymac.contacts" ]; then
    rm -f "$HOME/Library/Group Containers/N4RA379GBW.com.busymac.contacts" 2>/dev/null || true
fi

echo "Uninstallation complete!"
exit 0
