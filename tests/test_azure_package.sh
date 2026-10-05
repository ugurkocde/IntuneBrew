#!/bin/bash
# Build, expand and execute the dependency-complete package on a clean Mac runner.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
python "$root/.github/scripts/package_azure_cli.py" 2.90.0 "$stage/azure_cli_2.90.0.pkg"
pkgutil --expand-full "$stage/azure_cli_2.90.0.pkg" "$stage/expanded"
for arch in arm64 x86_64; do
  test -x "$stage/expanded/Payload/usr/local/lib/intunebrew/azure_cli/$arch/bin/python3.13"
done
AZURE_CONFIG_DIR="$stage/config" "$stage/expanded/Payload/usr/local/bin/az" version > "$stage/version.json"
python - "$stage/version.json" <<'PY'
import json, sys
assert json.load(open(sys.argv[1]))['azure-cli'] == '2.90.0'
PY
AZURE_CONFIG_DIR="$stage/config" "$stage/expanded/Payload/usr/local/bin/az" account list --output json > "$stage/accounts.json"
python - "$stage/accounts.json" <<'PY'
import json, sys
assert json.load(open(sys.argv[1])) == []
PY
echo 'Expanded Azure CLI runs without Homebrew or system Python'
if [ "${INSTALL_PACKAGE:-0}" = 1 ]; then
  sudo installer -pkg "$stage/azure_cli_2.90.0.pkg" -target /
  env PATH=/usr/bin:/bin AZURE_CONFIG_DIR="$stage/config" /usr/local/bin/az version > "$stage/installed-version.json"
  python - "$stage/installed-version.json" <<'PY'
import json, sys
assert json.load(open(sys.argv[1]))['azure-cli'] == '2.90.0'
PY
fi
