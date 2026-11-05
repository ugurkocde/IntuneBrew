#!/bin/bash
set -euo pipefail
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root" >&2
  exit 1
fi
# Never use shared PowerShell zap paths: stable installations share profiles.
if ! /usr/sbin/pkgutil --pkg-info com.microsoft.powershell-preview >/dev/null 2>&1; then
  echo "PowerShell Preview package is not installed; nothing removed."
  exit 0
fi
command="/usr/local/bin/pwsh-preview"
if [ -e "$command" ] || [ -L "$command" ]; then
  if [ ! -L "$command" ]; then
    echo "Refusing to remove a preview command owned by another installation" >&2
    exit 1
  fi
  case "$(/usr/bin/readlink "$command")" in
    /usr/local/microsoft/powershell/7-preview/pwsh|../microsoft/powershell/7-preview/pwsh) ;;
    *) echo "Refusing to remove a preview command owned by another installation" >&2; exit 1 ;;
  esac
fi
if [ -L /usr/local/microsoft/powershell/7-preview ] || [ -L /Applications/PowerShell-preview.app ]; then
  echo "Refusing to remove a replaced preview payload" >&2
  exit 1
fi
if [ -e /Applications/PowerShell-preview.app ]; then
  bundle=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' /Applications/PowerShell-preview.app/Contents/Info.plist)
  if [ "$bundle" != com.microsoft.powershell-preview ]; then
    echo "Refusing to remove an app owned by another installation" >&2
    exit 1
  fi
fi
/usr/bin/pkill -f '^/usr/local/microsoft/powershell/7-preview/pwsh( |$)' 2>/dev/null || true
/bin/rm -f -- "$command"
/bin/rm -rf -- /usr/local/microsoft/powershell/7-preview /Applications/PowerShell-preview.app
/usr/sbin/pkgutil --forget com.microsoft.powershell-preview
