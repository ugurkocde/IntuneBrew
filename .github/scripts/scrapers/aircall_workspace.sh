#!/bin/bash
set -euo pipefail
python3 "$(dirname "$0")/../collect_aircall_workspace.py"
