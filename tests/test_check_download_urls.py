import importlib.util
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_download_urls",
    ROOT / ".github/scripts/check_download_urls.py",
)
check_download_urls = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_download_urls)


class DownloadUrlHealthTests(unittest.TestCase):
    def response(self, status_code=200, content_type="application/octet-stream"):
        response = Mock()
        response.status_code = status_code
        response.headers = {"content-type": content_type}
        response.url = "https://downloads.example.test/app.dmg"
        return response

    def test_binary_response_is_healthy(self):
        response = self.response(status_code=206)

        with patch.object(check_download_urls.requests, "request", return_value=response):
            verdict, detail = check_download_urls.check_url(
                "https://downloads.example.test/app.dmg"
            )

        self.assertEqual(verdict, "ok")
        self.assertEqual(detail, "application/octet-stream")

    def test_html_response_is_broken_after_all_attempts(self):
        responses = [
            self.response(content_type="text/html; charset=utf-8")
            for _ in check_download_urls.ATTEMPTS
        ]

        with patch.object(check_download_urls.requests, "request", side_effect=responses):
            verdict, detail = check_download_urls.check_url(
                "https://downloads.example.test/missing.dmg"
            )

        self.assertEqual(verdict, "html_page")
        self.assertIn("returns an HTML page", detail)

    def test_request_failures_are_reported(self):
        failures = [
            check_download_urls.requests.ConnectionError("offline")
            for _ in check_download_urls.ATTEMPTS
        ]

        with patch.object(check_download_urls.requests, "request", side_effect=failures):
            verdict, detail = check_download_urls.check_url(
                "https://downloads.example.test/app.dmg"
            )

        self.assertEqual(verdict, "request_failed")
        self.assertEqual(detail, "ConnectionError")


if __name__ == "__main__":
    unittest.main()
