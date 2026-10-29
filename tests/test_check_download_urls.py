import importlib.util
import unittest
from pathlib import Path
from unittest.mock import Mock, PropertyMock, patch


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
        self.assertEqual(
            detail,
            "ConnectionError; attempts: HEAD/ib:ConnectionError; GET/ib:ConnectionError; "
            "GET/curl:ConnectionError; GET/browser:ConnectionError",
        )

    def test_html_challenge_records_each_attempt_without_reading_body(self):
        responses = [self.response(status_code=202, content_type="text/html; charset=utf-8")
                     for _ in check_download_urls.ATTEMPTS]
        body_accesses = []
        for response in responses:
            for attribute in ("text", "content"):
                prop = PropertyMock(side_effect=AssertionError("body must not be read"))
                setattr(type(response), attribute, prop)
                body_accesses.append(prop)
            response.iter_content.side_effect = AssertionError("body must not be streamed")

        with patch.object(check_download_urls.requests, "request", side_effect=responses) as request:
            verdict, detail = check_download_urls.check_url("https://downloads.example.test/app.dmg")

        self.assertEqual(verdict, "html_page")
        self.assertIn("HTTP 202 returns an HTML page", detail)
        self.assertTrue(detail.endswith(
            "attempts: HEAD/ib:202 text/html; GET/ib:202 text/html; "
            "GET/curl:202 text/html; GET/browser:202 text/html"))
        for body in body_accesses:
            body.assert_not_called()
        for response in responses:
            response.iter_content.assert_not_called()
            response.close.assert_called_once_with()
        self.assertEqual(request.call_count, 4)
        for call, attempt in zip(request.call_args_list, check_download_urls.ATTEMPTS):
            self.assertEqual(call.args, (attempt["method"], "https://downloads.example.test/app.dmg"))
            self.assertEqual(call.kwargs, {
                "headers": {"User-Agent": attempt["user_agent"],
                            **({"Range": "bytes=0-0"} if attempt["method"] == "GET" else {})},
                "timeout": 45, "allow_redirects": True, "stream": True,
            })

    def test_mixed_failures_keep_attempt_order_and_last_verdict(self):
        results = [self.response(status_code=403), self.response(status_code=202, content_type="text/html"),
                   check_download_urls.requests.ReadTimeout("sensitive exception message"),
                   self.response(status_code=202, content_type="text/html")]
        with patch.object(check_download_urls.requests, "request", side_effect=results):
            verdict, detail = check_download_urls.check_url("https://downloads.example.test/app.dmg")

        self.assertEqual(verdict, "html_page")
        self.assertTrue(detail.endswith(
            "attempts: HEAD/ib:403 application/octet-stream; GET/ib:202 text/html; "
            "GET/curl:ReadTimeout; GET/browser:202 text/html"))
        self.assertNotIn("sensitive", detail)

    def test_untrusted_media_type_is_replaced_in_summary(self):
        responses = [self.response(status_code=503, content_type="text/html|private\nvalue")
                     for _ in check_download_urls.ATTEMPTS]
        with patch.object(check_download_urls.requests, "request", side_effect=responses):
            verdict, detail = check_download_urls.check_url("https://downloads.example.test/app.dmg")

        self.assertEqual(verdict, "http_error")
        self.assertIn("HEAD/ib:503 unknown", detail)
        for forbidden in ("|", "\n", "private", "value"):
            self.assertNotIn(forbidden, detail)

    def test_later_binary_success_keeps_original_detail(self):
        content_type = "application/octet-stream; charset=binary"
        results = [self.response(status_code=202, content_type="text/html"),
                   self.response(status_code=206, content_type=content_type)]
        with patch.object(check_download_urls.requests, "request", side_effect=results) as request:
            result = check_download_urls.check_url("https://downloads.example.test/app.dmg")

        self.assertEqual(result, ("ok", content_type))
        self.assertEqual(request.call_count, 2)


if __name__ == "__main__":
    unittest.main()
