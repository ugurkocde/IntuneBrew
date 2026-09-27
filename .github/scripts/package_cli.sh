#!/bin/bash
# Package explicitly supported command-line archives without executing them.
set -euo pipefail
app_name=$1
extracted_dir=$2
version=$3
identifier=$4
case "$app_name" in
  1password_cli) source_dir=.; binaries=(op) ;;
  github_copilot_cli) source_dir=.; binaries=(copilot) ;;
  sentinel) source_dir=.; binaries=(sentinel) ;;
  android_sdk_platformtools) source_dir=platform-tools; binaries=(adb fastboot etc1tool hprof-conv make_f2fs make_f2fs_casefold mke2fs) ;;
  android_sdk_commandline_tools) source_dir=cmdline-tools; binaries=(bin/apkanalyzer bin/avdmanager bin/d8 bin/lint bin/profgen bin/r8 bin/resourceshrinker bin/retrace bin/screenshot2 bin/sdkmanager) ;;
  *) exit 0 ;;
esac
for binary in "${binaries[@]}"; do
  if [ ! -f "$extracted_dir/$source_dir/$binary" ]; then
    echo "Missing expected CLI payload: $binary" >&2
    exit 1
  fi
done
payload=$(mktemp -d)
trap 'rm -rf "$payload"' EXIT
install_dir="/usr/local/lib/intunebrew/$app_name"
mkdir -p "$payload$install_dir" "$payload/usr/local/bin"
ditto "$extracted_dir/$source_dir" "$payload$install_dir"
for binary in "${binaries[@]}"; do
  chmod 755 "$payload$install_dir/$binary"
  ln -s "$install_dir/$binary" "$payload/usr/local/bin/$(basename "$binary")"
done
pkgbuild --root "$payload" --identifier "$identifier" --version "$version" \
  --install-location / "$extracted_dir/${app_name}_${version}.pkg"
