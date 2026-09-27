#!/bin/bash
set -euo pipefail

# Microsoft moved its documentation; use the maintained Homebrew release record.
# Preserve the existing remotehelp catalog identity and enrichment fields.
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
curl --fail --silent --show-error --location --max-time 60 \
  'https://formulae.brew.sh/api/cask/microsoft-remote-help.json' > "$tmp"
jq -e '.disabled != true and .deprecated != true and
  (.version | type == "string" and length > 0) and
  (.url | startswith("https://")) and
  (.sha256 | test("^[a-fA-F0-9]{64}$"))' "$tmp" > /dev/null

mkdir -p Apps
existing='{}'
if [ -f Apps/remotehelp.json ]; then existing=$(cat Apps/remotehelp.json); fi
jq --argjson existing "$existing" '$existing * {
  name: "Remote Help", description: .desc, version: .version, url: .url,
  vendor_url: .url, homebrew_cask: .token, sha: .sha256,
  bundleId: "com.microsoft.remotehelp", homepage: .homepage,
  fileName: (.url | split("/") | last | split("?") | first), type: "pkg"
}' "$tmp" > Apps/remotehelp.json.tmp
mv Apps/remotehelp.json.tmp Apps/remotehelp.json
echo 'Updated Remote Help from Homebrew'
