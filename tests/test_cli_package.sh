#!/bin/bash
set -euo pipefail
script=$(cd "$(dirname "$0")/.." && pwd)/.github/scripts/package_cli.sh
fixture=$(mktemp -d)
trap 'rm -rf "$fixture"' EXIT
for name in 1password_cli github_copilot_cli codex_cli sentinel android_sdk_platformtools android_sdk_commandline_tools; do
  input="$fixture/$name"
  mkdir -p "$input"
  case "$name" in
    1password_cli) paths=(op); binary=op ;;
    github_copilot_cli) paths=(copilot); binary=copilot ;;
    codex_cli) paths=(bin/codex); binary=codex ;;
    sentinel) paths=(sentinel); binary=sentinel ;;
    android_sdk_platformtools) paths=(platform-tools/adb platform-tools/fastboot platform-tools/etc1tool platform-tools/hprof-conv platform-tools/make_f2fs platform-tools/make_f2fs_casefold platform-tools/mke2fs); binary=adb ;;
    android_sdk_commandline_tools) paths=(cmdline-tools/bin/apkanalyzer cmdline-tools/bin/avdmanager cmdline-tools/bin/d8 cmdline-tools/bin/lint cmdline-tools/bin/profgen cmdline-tools/bin/r8 cmdline-tools/bin/resourceshrinker cmdline-tools/bin/retrace cmdline-tools/bin/screenshot2 cmdline-tools/bin/sdkmanager); binary=sdkmanager ;;
  esac
  for item in "${paths[@]}"; do
    mkdir -p "$(dirname "$input/$item")"
    printf '#!/bin/sh\nexit 0\n' > "$input/$item"
  done
  if [ "$name" = codex_cli ]; then
    mkdir -p "$input/share/codex"
    printf 'support fixture\n' > "$input/share/codex/resources"
  fi
  bash "$script" "$name" "$input" 1.2.3 "com.intunebrew.$name"
  pkgutil --expand-full "$input/${name}_1.2.3.pkg" "$fixture/expanded-$name"
  test -L "$fixture/expanded-$name/Payload/usr/local/bin/$binary"
  grep -q 'version="1.2.3"' "$fixture/expanded-$name/PackageInfo"
  if [ "$name" = codex_cli ]; then
    test "$(readlink "$fixture/expanded-$name/Payload/usr/local/bin/codex")" = /usr/local/lib/intunebrew/codex_cli/bin/codex
    test -x "$fixture/expanded-$name/Payload/usr/local/lib/intunebrew/codex_cli/bin/codex"
    cmp "$input/share/codex/resources" "$fixture/expanded-$name/Payload/usr/local/lib/intunebrew/codex_cli/share/codex/resources"
    grep -q 'identifier="com.intunebrew.codex_cli"' "$fixture/expanded-$name/PackageInfo"
  fi
done
mkdir "$fixture/missing"
if bash "$script" sentinel "$fixture/missing" 1 com.intunebrew.sentinel; then
  echo 'Missing CLI executable unexpectedly packaged' >&2
  exit 1
fi
if bash "$script" codex_cli "$fixture/missing" 1 com.intunebrew.codex_cli; then
  echo 'Missing Codex CLI executable unexpectedly packaged' >&2
  exit 1
fi
printf 'CLI package layout checks passed\n'
