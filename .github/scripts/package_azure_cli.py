"""Build a relocatable Azure CLI PKG with Python and wheels for both Mac architectures."""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

PYTHON_VERSION = "3.13.16"
ARCHITECTURES = {"arm64": "aarch64", "x86_64": "x86_64"}


def build(version, output):
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Expected an Azure CLI release version")
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    uv = shutil.which("uv")
    if not uv:
        raise RuntimeError("Install uv==0.12.23 before building Azure CLI")
    with tempfile.TemporaryDirectory(prefix="azure-cli-package-") as directory:
        stage = Path(directory)
        payload = stage / "payload"
        install = payload / "usr/local/lib/intunebrew/azure_cli"
        for arch, uv_arch in ARCHITECTURES.items():
            downloads = stage / f"python-{arch}"
            request = f"cpython-{PYTHON_VERSION}-macos-{uv_arch}-none"
            subprocess.run([uv, "python", "install", "--no-bin", "--install-dir", str(downloads), request], check=True)
            runtime = install / arch
            shutil.copytree(downloads / request, runtime, symlinks=True)
            site = runtime / "lib/python3.13/site-packages"
            subprocess.run([uv, "pip", "install", "--no-config", "--python-version", PYTHON_VERSION,
                            "--python-platform", f"{uv_arch}-apple-darwin", "--only-binary", ":all:",
                            "--target", str(site), f"azure-cli=={version}"], check=True)
        binary = payload / "usr/local/bin/az"
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_text('''#!/bin/sh
set -eu
base="$(CDPATH= cd -- "$(dirname -- "$0")/../lib/intunebrew/azure_cli" && pwd)"
case "$(/usr/bin/uname -m)" in
  arm64) runtime="$base/arm64" ;;
  x86_64) runtime="$base/x86_64" ;;
  *) echo "Unsupported Mac architecture" >&2; exit 1 ;;
esac
export PYTHONNOUSERSITE=1
unset PYTHONHOME PYTHONPATH
exec "$runtime/bin/python3.13" -s -m azure.cli "$@"
''')
        binary.chmod(0o755)
        # Exercise the staged, relocatable runtime, never the runner's Homebrew az.
        result = subprocess.check_output([str(binary), "version"], env={**os.environ, "AZURE_CONFIG_DIR": str(stage / "config")})
        import json
        if json.loads(result).get("azure-cli") != version:
            raise RuntimeError("Bundled Azure CLI did not report the requested version")
        subprocess.run(["pkgbuild", "--root", str(payload), "--identifier", "com.intunebrew.azure_cli",
                        "--version", version, "--install-location", "/", str(output)], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("version")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build(args.version, args.output)
