#!/bin/bash
# Recognize the UDIF trailer without mounting or executing the downloaded file.
set -euo pipefail
[ "$#" -eq 1 ] && [ -f "$1" ] || exit 1
size=$(wc -c < "$1")
[ "$size" -ge 512 ] || exit 1
signature=$(tail -c 512 "$1" | od -An -N4 -tx1 | tr -d ' \n')
[ "$signature" = 6b6f6c79 ]
