"""Track Aircall's official Workspace installer independently of legacy Aircall."""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse, unquote

import requests

SOURCE = "https://electron.aircall.io/download/osx?appType=aircall-workspace&arch=arm64&platform=macPkg"


def collect():
    path = Path("Apps/aircall_workspace.json")
    previous = json.loads(path.read_text()) if path.exists() else {}
    with requests.get(SOURCE, stream=True, timeout=(30, 120)) as response:
        response.raise_for_status()
        url = urlparse(response.url)
        filename = unquote(url.path.rsplit("/", 1)[-1])
        match = re.fullmatch(r"Aircall-Workspace-([0-9]+(?:\.[0-9]+)+)-arm64\.pkg", filename)
        if url.scheme != "https" or url.hostname != "download-electron.aircall.io" or not match:
            raise ValueError("Unexpected Aircall Workspace download location")
        version = match.group(1)
        sha = previous.get("sha", "")
        if previous.get("url") != response.url or not re.fullmatch(r"[a-fA-F0-9]{64}", sha):
            digest = hashlib.sha256()
            size = 0
            for chunk in response.iter_content(1024 * 1024):
                if not chunk:
                    continue
                if size == 0 and not chunk.startswith(b"xar!"):
                    raise ValueError("Aircall download is not a PKG archive")
                size += len(chunk)
                if size > 2 * 1024**3:
                    raise ValueError("Aircall installer exceeds the download limit")
                digest.update(chunk)
            if not size:
                raise ValueError("Empty Aircall installer")
            sha = digest.hexdigest()
        data = {**previous, "name": "Aircall Workspace", "description": "Aircall calling and messaging workspace",
                "version": version, "previous_version": previous.get("version", version),
                "url": response.url, "vendor_url": response.url, "sha": sha,
                "bundleId": "io.aircall.workspace", "homepage": "https://aircall.io/download/",
                "fileName": filename, "type": "pkg", "publisher": "Aircall", "category": "Communication"}
    path.parent.mkdir(exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(path)
    print(f"Updated Aircall Workspace to {version}")


if __name__ == "__main__":
    collect()
