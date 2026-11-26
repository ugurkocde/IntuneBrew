import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / ".github/scripts"
sys.path.insert(0, str(SCRIPTS))
import collect_app_info as collect


class MagnificDesktopCollectorTests(unittest.TestCase):
    def setUp(self):
        self.spec = next(
            app for app in collect.DIRECT_VENDOR_DMG_APPS if app.slug == "magnific_desktop"
        )

    def test_collect_writes_verified_versioned_url_and_tracks_previous_version(self):
        with tempfile.TemporaryDirectory() as root:
            calls = []
            manifest_urls = []

            def fake_manifest(url):
                manifest_urls.append(url)
                return {"version": "1.5.7"}

            def fake_inspect(url, bundle_id, *, team_id=None):
                calls.append((url, bundle_id, team_id))
                return collect.SignedBundleObservation(
                    artifact_sha256="a" * 64,
                    bundle_id=bundle_id,
                    short_version="1.5.7",
                    bundle_version="1.5.7",
                    team_id=team_id,
                )

            first = collect.collect_direct_vendor_dmg(
                self.spec,
                apps_folder=root,
                inspect=fake_inspect,
                fetch_manifest=fake_manifest,
            )
            expected_url_157 = "https://cdn.magnific.com/ait/magnific-desktop/1.5.7/macos-aarch64.dmg"
            self.assertEqual(manifest_urls, [self.spec.manifest_url])
            self.assertEqual(
                calls,
                [(expected_url_157, "com.freepik.magnific.desktop", "CCAL5Z426N")],
            )
            self.assertEqual(first["version"], "1.5.7")
            self.assertEqual(first["previous_version"], "1.5.7")
            self.assertEqual(first["url"], expected_url_157)
            self.assertEqual(first["vendor_url"], expected_url_157)
            self.assertEqual(first["bundleIdEvidence"]["url"], expected_url_157)
            self.assertEqual(first["sha"], "a" * 64)
            self.assertEqual(first["bundleId"], "com.freepik.magnific.desktop")
            self.assertEqual(first["bundleIdEvidence"]["teamId"], "CCAL5Z426N")

            def fake_upgrade(url, bundle_id, *, team_id=None):
                return collect.SignedBundleObservation(
                    artifact_sha256="b" * 64,
                    bundle_id=bundle_id,
                    short_version="1.6.0",
                    bundle_version="1.6.0",
                    team_id=team_id,
                )

            second = collect.collect_direct_vendor_dmg(
                self.spec,
                apps_folder=root,
                inspect=fake_upgrade,
                fetch_manifest=lambda _url: {"version": "1.6.0"},
            )
            expected_url_160 = "https://cdn.magnific.com/ait/magnific-desktop/1.6.0/macos-aarch64.dmg"
            self.assertEqual(second["version"], "1.6.0")
            self.assertEqual(second["previous_version"], "1.5.7")
            self.assertEqual(second["url"], expected_url_160)
            saved = json.loads((Path(root) / "magnific_desktop.json").read_text())
            self.assertEqual(saved["version"], "1.6.0")
            self.assertEqual(saved["url"], expected_url_160)
            self.assertEqual(saved["sha"], "b" * 64)

    def test_refusal_preserves_existing_catalog_entry(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "magnific_desktop.json"
            original = {"name": "Magnific Desktop", "version": "1.5.7", "sha": "a" * 64}
            target.write_text(json.dumps(original))

            def fake_refusal(url, bundle_id, *, team_id=None):
                return collect.InspectionRefusal("SIGNATURE_IDENTITY_INVALID", True)

            with self.assertRaisesRegex(ValueError, "SIGNATURE_IDENTITY_INVALID"):
                collect.collect_direct_vendor_dmg(
                    self.spec,
                    apps_folder=root,
                    inspect=fake_refusal,
                    fetch_manifest=lambda _url: {"version": "1.5.7"},
                )
            self.assertEqual(json.loads(target.read_text()), original)

    def test_missing_whitespace_or_mismatched_version_refused(self):
        with tempfile.TemporaryDirectory() as root:
            for bad_manifest in ("", " ", "1.5.7 ", "../1.5.7", "1.5.7/evil"):
                with self.assertRaisesRegex(ValueError, "manifest invalid version"):
                    collect.collect_direct_vendor_dmg(
                        self.spec,
                        apps_folder=root,
                        inspect=lambda *args, **kwargs: self.fail("inspect must not run"),
                        fetch_manifest=lambda _url, _v=bad_manifest: {"version": _v},
                    )
            for bad_signed in ("", " ", "1.5.7 ", " 1.5.7"):
                def fake_bad_version(url, bundle_id, *, team_id=None, _v=bad_signed):
                    return collect.SignedBundleObservation(
                        artifact_sha256="a" * 64,
                        bundle_id=bundle_id,
                        short_version=_v,
                        bundle_version=_v,
                        team_id=team_id,
                    )

                with self.assertRaisesRegex(ValueError, "invalid version"):
                    collect.collect_direct_vendor_dmg(
                        self.spec,
                        apps_folder=root,
                        inspect=fake_bad_version,
                        fetch_manifest=lambda _url: {"version": "1.5.7"},
                    )
            with self.assertRaisesRegex(ValueError, "version mismatch"):
                collect.collect_direct_vendor_dmg(
                    self.spec,
                    apps_folder=root,
                    inspect=lambda url, bundle_id, *, team_id=None: collect.SignedBundleObservation(
                        artifact_sha256="a" * 64,
                        bundle_id=bundle_id,
                        short_version="1.5.8",
                        bundle_version="1.5.8",
                        team_id=team_id,
                    ),
                    fetch_manifest=lambda _url: {"version": "1.5.7"},
                )
            self.assertFalse((Path(root) / "magnific_desktop.json").exists())

    def test_deadline_and_timeout_error_converted_to_value_error(self):
        with tempfile.TemporaryDirectory() as root:
            for exc_cls in (collect._StableReleaseDeadline, TimeoutError):
                def fake_slow(url, bundle_id, *, team_id=None, _cls=exc_cls):
                    raise _cls("timed out")

                with self.assertRaisesRegex(ValueError, "aborted"):
                    collect.collect_direct_vendor_dmg(
                        self.spec,
                        apps_folder=root,
                        inspect=fake_slow,
                        fetch_manifest=lambda _url: {"version": "1.5.7"},
                    )
            self.assertFalse((Path(root) / "magnific_desktop.json").exists())

    def test_write_uses_unique_temp_file_and_cleans_up_on_replace_failure(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "magnific_desktop.json"
            original = {"name": "Magnific Desktop", "version": "1.5.7", "sha": "a" * 64}
            target.write_text(json.dumps(original))

            def fake_inspect(url, bundle_id, *, team_id=None):
                return collect.SignedBundleObservation(
                    artifact_sha256="b" * 64,
                    bundle_id=bundle_id,
                    short_version="1.6.0",
                    bundle_version="1.6.0",
                    team_id=team_id,
                )

            seen_temps = []

            def fail_replace(src, dst):
                seen_temps.append(src)
                raise OSError("simulated replace failure")

            with mock.patch.object(os, "replace", side_effect=fail_replace):
                with self.assertRaises(OSError):
                    collect.collect_direct_vendor_dmg(
                        self.spec,
                        apps_folder=root,
                        inspect=fake_inspect,
                        fetch_manifest=lambda _url: {"version": "1.6.0"},
                    )
            self.assertEqual(len(seen_temps), 1)
            self.assertNotEqual(seen_temps[0], f"{target}.tmp")
            self.assertFalse(Path(seen_temps[0]).exists())
            self.assertEqual(json.loads(target.read_text()), original)

    def test_fetch_direct_vendor_manifest_rejects_oversized_and_redirect_without_draining(self):
        from http.server import BaseHTTPRequestHandler, HTTPServer
        import threading

        redirect_body_sent = {"bytes": 0}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                return

            def do_GET(self):
                if self.path == "/oversized":
                    body = b"x" * (collect.DIRECT_VENDOR_MANIFEST_MAX_BYTES + 4096)
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    try:
                        self.wfile.write(body)
                    except OSError:
                        pass
                elif self.path == "/redirect":
                    self.send_response(302)
                    self.send_header("Location", "/ok")
                    self.send_header("Content-Length", str(4 * 1024 * 1024))
                    self.end_headers()
                    chunk = b"r" * 65536
                    try:
                        for _ in range(64):
                            self.wfile.write(chunk)
                            self.wfile.flush()
                            redirect_body_sent["bytes"] += len(chunk)
                    except OSError:
                        pass
                elif self.path == "/bad-bytes":
                    body = b"\x1f\x8b\x08\x00invalid-gzip-payload"
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                elif self.path == "/nan":
                    body = b'{"version": "1.5.7", "extra": NaN}'
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                elif self.path == "/deep":
                    body = b"[" * 100000
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    body = json.dumps({"version": "1.5.7"}).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

        server = HTTPServer(("127.0.0.1", 0), Handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            self.assertEqual(
                collect._fetch_direct_vendor_manifest(f"http://127.0.0.1:{port}/ok"),
                {"version": "1.5.7"},
            )
            with self.assertRaisesRegex(ValueError, "exceeded"):
                collect._fetch_direct_vendor_manifest(f"http://127.0.0.1:{port}/oversized")
            with self.assertRaisesRegex(ValueError, "HTTP 302"):
                collect._fetch_direct_vendor_manifest(f"http://127.0.0.1:{port}/redirect")
            with self.assertRaisesRegex(ValueError, "invalid JSON"):
                collect._fetch_direct_vendor_manifest(f"http://127.0.0.1:{port}/bad-bytes")
            with self.assertRaisesRegex(ValueError, "invalid JSON"):
                collect._fetch_direct_vendor_manifest(f"http://127.0.0.1:{port}/nan")
            with self.assertRaisesRegex(ValueError, "invalid JSON"):
                collect._fetch_direct_vendor_manifest(f"http://127.0.0.1:{port}/deep")
            self.assertLess(redirect_body_sent["bytes"], 4 * 1024 * 1024)
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
