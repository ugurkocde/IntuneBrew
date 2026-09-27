import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / '.github/scripts/download_vendor.sh'

class VendorDownloadTests(unittest.TestCase):
    def test_client_fallback_replaces_partial_failed_download(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            curl = root / 'curl'
            curl.write_text('''#!/bin/bash
output=""
custom=false
while [ $# -gt 0 ]; do
  case "$1" in
    -o) output=$2; shift ;;
    --user-agent) custom=true; shift ;;
  esac
  shift
done
if [ "$custom" = true ]; then
  printf partial > "$output"
  exit 22
fi
[ ! -e "$output" ] || exit 9
printf complete > "$output"
''')
            curl.chmod(0o755)
            output = root / 'installer'
            environment = dict(os.environ, PATH=f"{root}:{os.environ['PATH']}")
            subprocess.run(['bash', str(SCRIPT), 'https://vendor.test/app', str(output)], env=environment, check=True)
            self.assertEqual(output.read_text(), 'complete')

    def test_all_clients_failing_leaves_no_package(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            curl = root / 'curl'
            curl.write_text('#!/bin/sh\nexit 22\n')
            curl.chmod(0o755)
            output = root / 'installer'
            output.write_text('old partial download')
            environment = dict(os.environ, PATH=f"{root}:{os.environ['PATH']}")
            result = subprocess.run(['bash', str(SCRIPT), 'https://vendor.test/app', str(output)], env=environment)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())
