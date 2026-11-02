#!/bin/bash
set -euo pipefail
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root" >&2
  exit 1
fi
# A refused installation must never authorize removal of another Git's files.
if ! pkgutil --pkg-info com.intunebrew.git_gui >/dev/null 2>&1; then
  echo "Git GUI package is not installed; nothing removed."
  exit 0
fi
# Check every command before deleting anything. Preserve a later replacement.
for command in git-gui git-citool gitk; do
  path="/usr/local/bin/$command"
  if [ -e "$path" ] || [ -L "$path" ]; then
    if [ -L "$path" ] || ! /usr/bin/grep -Fq '../lib/intunebrew/git_gui' "$path"; then
      echo "Refusing to remove $command owned by another installation" >&2
      exit 1
    fi
  fi
done
pkill -f '/usr/local/lib/intunebrew/git_gui/' 2>/dev/null || true
rm -f /usr/local/bin/git-gui /usr/local/bin/git-citool /usr/local/bin/gitk
rm -rf /usr/local/lib/intunebrew/git_gui
pkgutil --forget com.intunebrew.git_gui
