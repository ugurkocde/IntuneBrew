#!/bin/bash
# Build and run the package in a fresh Mac runner; installation is CI-only opt-in.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
version=$(python - <<'PYVERSION'
import json, re
from urllib.request import urlopen
with urlopen("https://formulae.brew.sh/api/formula/git-gui.json", timeout=30) as response:
    version = json.load(response)["versions"]["stable"]
assert re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version)
print(version)
PYVERSION
)
python "$root/.github/scripts/package_git_gui.py" "$version" "$stage/git_gui.pkg"
pkgutil --expand-full "$stage/git_gui.pkg" "$stage/expanded"
payload="$stage/expanded/Payload"
base="$payload/usr/local/lib/intunebrew/git_gui"
python "$root/tests/verify_git_gui_payload.py" "$payload"
env PATH=/usr/bin:/bin "$payload/usr/local/bin/git-gui" --version | grep '^git-gui version '
if [ "${INSTALL_PACKAGE:-0}" = 1 ]; then
  # Never replace an existing runner installation as part of this fixture.
  for command in git-gui git-citool gitk; do
    test ! -e "/usr/local/bin/$command"
    test ! -L "/usr/local/bin/$command"
  done
  test ! -e /usr/local/lib/intunebrew/git_gui
  if pkgutil --pkg-info com.intunebrew.git_gui; then
    echo 'Runner already has a Git GUI package receipt' >&2
    exit 1
  fi
  printf '%s\n' '{"name":"Git GUI","homebrew_formula":"git-gui","packaging_recipe":"git-gui-tcltk-v1"}' > "$stage/app.json"
  python "$root/.github/scripts/generate_uninstall_scripts.py" --apps "$stage/app.json" --output "$stage/uninstall"
  # A refused/nonexistent installation cannot authorize deleting a foreign link.
  printf '%s\n' '#!/bin/sh' 'echo foreign-gitk-fixture' > "$stage/foreign-gitk"
  sudo mkdir -p /usr/local/bin
  sudo ln -s "$stage/foreign-gitk" /usr/local/bin/gitk
  sudo bash "$stage/uninstall/uninstall_git_gui.sh"
  test "$(readlink /usr/local/bin/gitk)" = "$stage/foreign-gitk"
  sudo rm /usr/local/bin/gitk
  sudo installer -pkg "$stage/git_gui.pkg" -target /
  env PATH=/usr/bin:/bin /usr/local/bin/git-gui --version | grep '^git-gui version '
  pkgutil --pkg-info com.intunebrew.git_gui
  python "$root/tests/verify_git_gui_payload.py" /
  # Preserve a foreign replacement even when our old package receipt exists.
  sudo mv /usr/local/bin/gitk "$stage/owned-gitk"
  sudo ln -s "$stage/foreign-gitk" /usr/local/bin/gitk
  if sudo bash "$stage/uninstall/uninstall_git_gui.sh"; then
    echo 'Uninstall accepted a foreign replacement' >&2
    exit 1
  fi
  test "$(readlink /usr/local/bin/gitk)" = "$stage/foreign-gitk"
  test -f /usr/local/bin/git-gui
  test -d /usr/local/lib/intunebrew/git_gui
  sudo rm /usr/local/bin/gitk
  sudo mv "$stage/owned-gitk" /usr/local/bin/gitk
  # Exercise positive cleanup using the actual generated uninstall script.
  sudo bash "$stage/uninstall/uninstall_git_gui.sh"
  test ! -e /usr/local/bin/git-gui
  test ! -e /usr/local/bin/git-citool
  test ! -e /usr/local/bin/gitk
  test ! -e /usr/local/lib/intunebrew/git_gui
  if pkgutil --pkg-info com.intunebrew.git_gui; then
    echo 'Git GUI receipt remained after cleanup' >&2
    exit 1
  fi
fi
