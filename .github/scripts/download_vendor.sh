#!/bin/bash
# Public vendor CDNs differ in which ordinary download clients they accept.
set -euo pipefail
url=$1
output=$2
for user_agent in 'Mozilla/5.0' ''; do
  args=(-f -L --retry 3 --connect-timeout 30 --max-time 600 -o "$output")
  if [ -n "$user_agent" ]; then args+=(--user-agent "$user_agent"); fi
  if curl "${args[@]}" "$url"; then exit 0; fi
  rm -f "$output"
done
exit 1
