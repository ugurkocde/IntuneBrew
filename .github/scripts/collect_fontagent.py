"""Read FontAgent's release metadata from the vendor's signed installer."""
import hashlib
import json
from pathlib import Path
import plistlib
import re
import subprocess
import tempfile

import requests

SOURCE = "https://store.insidersoftware.com/_downloads/FontAgent.dmg"
BUNDLE_ID = "com.insidersoftware.v9.fontagent"


def read_metadata(expanded):
    matches = list(Path(expanded).glob("*/Payload/Applications/*/FontAgent.app/Contents/Info.plist"))
    if len(matches) != 1:
        raise ValueError("Expected exactly one FontAgent application in the installer")
    with matches[0].open("rb") as stream:
        info = plistlib.load(stream)
    version = info.get("CFBundleShortVersionString", "")
    if info.get("CFBundleIdentifier") != BUNDLE_ID or not re.fullmatch(r"\d+(?:\.\d+)+", version):
        raise ValueError("Unexpected FontAgent identity or version")
    return version


def inspect_installer(dmg, stage):
    mount = stage / "mount"
    mount.mkdir()
    subprocess.run(["hdiutil", "attach", "-readonly", "-nobrowse", "-mountpoint", str(mount), str(dmg)], check=True)
    try:
        packages = list(mount.glob("*.pkg"))
        if len(packages) != 1:
            raise ValueError("Expected exactly one FontAgent installer")
        signature = subprocess.check_output(["pkgutil", "--check-signature", str(packages[0])], text=True)
        if "Developer ID Installer: Insider Software Inc. (936VDEB3YQ)" not in signature:
            raise ValueError("Unexpected FontAgent installer signer")
        expanded = stage / "expanded"
        subprocess.run(["pkgutil", "--expand-full", str(packages[0]), str(expanded)], check=True)
        return read_metadata(expanded)
    finally:
        subprocess.run(["hdiutil", "detach", str(mount)], check=True)


def collect():
    path = Path("Apps/fontagent.json")
    previous = json.loads(path.read_text()) if path.exists() else {}
    with tempfile.TemporaryDirectory(prefix="fontagent-") as directory:
        stage = Path(directory)
        dmg = stage / "FontAgent.dmg"
        digest = hashlib.sha256()
        size = 0
        with requests.get(SOURCE, stream=True, timeout=(30, 120)) as response:
            response.raise_for_status()
            with dmg.open("wb") as stream:
                for chunk in response.iter_content(1024 * 1024):
                    size += len(chunk)
                    if size > 2 * 1024**3:
                        raise ValueError("FontAgent installer exceeds the download limit")
                    stream.write(chunk)
                    digest.update(chunk)
        version = inspect_installer(dmg, stage)
    data = {**previous, "name": "FontAgent", "description": "Font management and activation for macOS",
            "version": version, "previous_version": previous.get("version", version),
            "url": SOURCE, "vendor_url": SOURCE, "sha": digest.hexdigest(),
            "bundleId": BUNDLE_ID, "homepage": "https://www.insidersoftware.com/fontagent-trial/",
            "fileName": "FontAgent.dmg", "type": "pkg_in_dmg", "publisher": "Insider Software",
            "custom_source": "fontagent"}
    path.parent.mkdir(exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(path)
    print(f"Collected FontAgent {version}; vendor PKG ready for extraction and publication")


if __name__ == "__main__":
    collect()
