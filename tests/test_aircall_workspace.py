import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

SPEC = importlib.util.spec_from_file_location("aircall", Path(__file__).resolve().parents[1] / ".github/scripts/collect_aircall_workspace.py")
aircall = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(aircall)
URL = "https://download-electron.aircall.io/aircall-workspace/Aircall-Workspace-1.18.1-arm64.pkg"


class AircallTests(unittest.TestCase):
    def response(self, url=URL, payload=b"xar!vendor fixture"):
        response = MagicMock()
        response.__enter__.return_value = response
        response.url = url
        response.iter_content.return_value = [payload]
        return response

    def test_hashes_download_and_reuses_versioned_installer(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.chdir(tmp):
            response = self.response()
            with patch.object(aircall.requests, "get", return_value=response):
                aircall.collect()
            data = json.loads(Path("Apps/aircall_workspace.json").read_text())
            self.assertEqual(data["sha"], hashlib.sha256(b"xar!vendor fixture").hexdigest())
            self.assertEqual(data["version"], "1.18.1")
            response = self.response()
            with patch.object(aircall.requests, "get", return_value=response):
                aircall.collect()
            response.iter_content.assert_not_called()

    def test_rejects_unexpected_redirect_and_html_without_overwriting(self):
        for response in [self.response(url="https://example.test/Aircall-Workspace-1.18.1-arm64.pkg"), self.response(payload=b"<html>unavailable</html>")]:
            with self.subTest(url=response.url), tempfile.TemporaryDirectory() as tmp, contextlib.chdir(tmp):
                Path("Apps").mkdir()
                path = Path("Apps/aircall_workspace.json")
                path.write_text('{"version":"1.17.0"}')
                with patch.object(aircall.requests, "get", return_value=response):
                    with self.assertRaises(ValueError):
                        aircall.collect()
                self.assertEqual(json.loads(path.read_text()), {"version":"1.17.0"})
