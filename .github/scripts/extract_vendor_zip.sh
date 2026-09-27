#!/bin/bash
# Some valid vendor ZIPs carry trailing data beyond unzip's directory search window.
set -euo pipefail
archive=$1
destination=$2
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
if ! unzip -q "$archive" -d "$scratch"; then
  echo 'Retrying ZIP extraction with the macOS streaming archive reader'
  rm -rf "$scratch"
  mkdir -p "$scratch"
  tar -xf "$archive" -C "$scratch"
fi
ditto "$scratch" "$destination"
