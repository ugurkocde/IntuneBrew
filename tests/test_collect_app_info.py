import contextlib
import importlib.util
import io
import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "collect_app_info",
    ROOT / ".github/scripts/collect_app_info.py",
)
collect_app_info = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(collect_app_info)


def cask_response(payload=None, status_code=200):
    """Build a fake requests response for one cask JSON fetch."""
    response = Mock(status_code=status_code)
    if status_code >= 400:
        response.raise_for_status.side_effect = collect_app_info.requests.HTTPError(
            response=response
        )
    else:
        response.raise_for_status.return_value = None
        response.json.return_value = payload
    return response


class CountingSession:
    """Stands in for the module-level session and records every URL it is asked for."""

    def __init__(self, responses):
        self.responses = responses
        self.requested = []

    def get(self, url, **kwargs):
        self.requested.append(url)
        return self.responses[url]


class CollectAppInfoTests(unittest.TestCase):
    def setUp(self):
        collect_app_info.cask_cache.clear()

    def tearDown(self):
        collect_app_info.cask_cache.clear()

    def test_homebrew_404_is_reported_as_removed_cask(self):
        response = Mock(status_code=404)
        response.raise_for_status.side_effect = collect_app_info.requests.HTTPError(response=response)

        with patch.object(collect_app_info, "cask_session", Mock(get=Mock(return_value=response))):
            with self.assertRaises(collect_app_info.CaskUnavailableError) as context:
                collect_app_info.get_homebrew_app_info(
                    "https://formulae.brew.sh/api/cask/removed-app.json"
                )

        self.assertEqual(context.exception.cask_token, "removed-app")
        self.assertIsNone(context.exception.display_name)
        self.assertEqual(context.exception.reason, "cask removed from Homebrew")

    def test_non_404_homebrew_error_is_not_treated_as_deprecation(self):
        response = Mock(status_code=503)
        response.raise_for_status.side_effect = collect_app_info.requests.HTTPError(response=response)

        with patch.object(collect_app_info, "cask_session", Mock(get=Mock(return_value=response))):
            with self.assertRaises(collect_app_info.requests.HTTPError):
                collect_app_info.get_homebrew_app_info(
                    "https://formulae.brew.sh/api/cask/temporarily-unavailable.json"
                )

    def test_disabled_cask_preserves_display_name_and_token(self):
        response = Mock(status_code=200)
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "name": ["Example App"],
            "deprecated": False,
            "disabled": True,
            "disable_reason": "discontinued",
        }

        with patch.object(collect_app_info, "cask_session", Mock(get=Mock(return_value=response))):
            with self.assertRaises(collect_app_info.CaskUnavailableError) as context:
                collect_app_info.get_homebrew_app_info(
                    "https://formulae.brew.sh/api/cask/example-app.json"
                )

        self.assertEqual(context.exception.display_name, "Example App")
        self.assertEqual(context.exception.cask_token, "example-app")
        self.assertEqual(
            context.exception.reason,
            "disabled in Homebrew: discontinued",
        )

    def test_removed_cask_marks_matching_app_deprecated(self):
        with tempfile.TemporaryDirectory() as directory:
            app_path = Path(directory) / "vmware_fusion.json"
            app_path.write_text(
                json.dumps({"name": "VMware Fusion", "version": "13.6.3"}),
                encoding="utf-8",
            )

            changed = collect_app_info.mark_app_deprecated(
                directory,
                display_name=None,
                reason="cask removed from Homebrew",
                cask_token="vmware-fusion",
            )

            self.assertTrue(changed)
            app_data = json.loads(app_path.read_text(encoding="utf-8"))
            self.assertTrue(app_data["deprecated"])
            self.assertEqual(
                app_data["deprecation_reason"],
                "cask removed from Homebrew",
            )
            self.assertEqual(app_data["homebrew_cask"], "vmware-fusion")

    def test_stored_cask_provenance_resolves_nonstandard_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            app_path = Path(directory) / "custom_filename.json"
            app_path.write_text(
                json.dumps(
                    {
                        "name": "Different Display Name",
                        "homebrew_cask": "source-token",
                    }
                ),
                encoding="utf-8",
            )

            resolved = collect_app_info.find_app_file(
                directory,
                cask_token="source-token",
            )

            self.assertEqual(resolved, str(app_path))


CASK_INFO = {
    "https://formulae.brew.sh/api/cask/tailscale.json": {
        "name": "Tailscale",
        "description": "Mesh VPN",
        "version": "1.80.0",
        "url": "https://example.com/tailscale-1.80.0.dmg",
        "vendor_url": "https://example.com/tailscale-1.80.0.dmg",
        "bundleId": "io.tailscale.ipn.macos",
        "homepage": "https://tailscale.com/",
        "homebrew_cask": "tailscale",
        "fileName": "tailscale-1.80.0.dmg",
    },
    "https://formulae.brew.sh/api/cask/tailscale-app.json": {
        "name": "Tailscale",
        "description": "Mesh VPN",
        "version": "1.82.0",
        "url": "https://example.com/tailscale-app-1.82.0.dmg",
        "vendor_url": "https://example.com/tailscale-app-1.82.0.dmg",
        "bundleId": "io.tailscale.ipn.macsys",
        "homepage": "https://tailscale.com/",
        "homebrew_cask": "tailscale-app",
        "fileName": "tailscale-app-1.82.0.dmg",
    },
}


def fake_get_homebrew_app_info(json_url, **kwargs):
    return dict(CASK_INFO[json_url])


@contextlib.contextmanager
def run_collector(work_dir, cask_urls, session=None):
    """Run main() against a scratch Apps folder with no network and no README writes.

    Without a session the prefetch is stubbed out and app info comes from CASK_INFO.
    With one, the real prefetch and the real get_homebrew_app_info run against it.
    """
    previous_dir = os.getcwd()
    os.chdir(work_dir)
    output = io.StringIO()
    try:
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(collect_app_info, "app_urls", []))
            stack.enter_context(patch.object(collect_app_info, "homebrew_cask_urls", cask_urls))
            stack.enter_context(patch.object(collect_app_info, "pkg_in_pkg_urls", []))
            stack.enter_context(patch.object(collect_app_info, "pkg_urls", []))
            stack.enter_context(patch.object(collect_app_info, "pkg_in_dmg_urls", []))
            stack.enter_context(patch.object(collect_app_info, "custom_scrapers", []))
            stack.enter_context(patch.dict(collect_app_info.cask_cache, {}, clear=True))
            if session is None:
                stack.enter_context(patch.object(collect_app_info, "prefetch_cask_data", Mock()))
                stack.enter_context(
                    patch.object(
                        collect_app_info, "get_homebrew_app_info", fake_get_homebrew_app_info
                    )
                )
            else:
                stack.enter_context(patch.object(collect_app_info, "cask_session", session))
            stack.enter_context(
                patch.object(collect_app_info, "calculate_file_hash", Mock(return_value="0" * 64))
            )
            stack.enter_context(patch.object(collect_app_info, "update_readme_apps", Mock()))
            stack.enter_context(
                patch.object(collect_app_info, "update_readme_with_latest_changes", Mock())
            )
            stack.enter_context(contextlib.redirect_stdout(output))
            yield output
    finally:
        os.chdir(previous_dir)


class FilenameCollisionTests(unittest.TestCase):
    def setUp(self):
        del collect_app_info.filename_collisions[:]

    def tearDown(self):
        del collect_app_info.filename_collisions[:]

    def write_app(self, directory, name, data):
        path = Path(directory) / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_missing_file_is_claimable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "tailscale.json")

            self.assertTrue(collect_app_info.claim_app_file(path, "tailscale"))
            self.assertEqual(collect_app_info.filename_collisions, [])

    def test_matching_cask_is_claimable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_app(
                directory, "tailscale.json", {"name": "Tailscale", "homebrew_cask": "tailscale"}
            )

            self.assertTrue(collect_app_info.claim_app_file(str(path), "tailscale"))
            self.assertEqual(collect_app_info.filename_collisions, [])

    def test_absent_or_empty_cask_is_claimable(self):
        with tempfile.TemporaryDirectory() as directory:
            missing_key = self.write_app(directory, "no_key.json", {"name": "Tailscale"})
            empty_value = self.write_app(
                directory, "empty.json", {"name": "Tailscale", "homebrew_cask": ""}
            )

            self.assertTrue(collect_app_info.claim_app_file(str(missing_key), "tailscale"))
            self.assertTrue(collect_app_info.claim_app_file(str(empty_value), "tailscale"))
            self.assertEqual(collect_app_info.filename_collisions, [])

    def test_foreign_cask_is_refused_and_recorded(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_app(
                directory, "tailscale.json", {"name": "Tailscale", "homebrew_cask": "tailscale"}
            )

            self.assertFalse(collect_app_info.claim_app_file(str(path), "tailscale-app"))
            self.assertEqual(
                collect_app_info.filename_collisions,
                [
                    {
                        "file_path": str(path),
                        "existing_cask": "tailscale",
                        "incoming_cask": "tailscale-app",
                    }
                ],
            )

    def test_deprecated_target_is_guarded_like_any_other_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_app(
                directory,
                "tailscale.json",
                {"name": "Tailscale", "homebrew_cask": "tailscale", "deprecated": True},
            )

            self.assertFalse(collect_app_info.claim_app_file(str(path), "tailscale-app"))
            self.assertEqual(len(collect_app_info.filename_collisions), 1)

    def test_mark_app_deprecated_refuses_foreign_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_app(
                directory, "tailscale.json", {"name": "Tailscale", "homebrew_cask": "tailscale"}
            )
            before = path.read_bytes()

            changed = collect_app_info.mark_app_deprecated(
                directory,
                display_name="Tailscale",
                reason="cask removed from Homebrew",
                cask_token="tailscale-app",
            )

            self.assertFalse(changed)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(len(collect_app_info.filename_collisions), 1)

    def test_second_cask_does_not_overwrite_first_writer(self):
        with tempfile.TemporaryDirectory() as directory:
            os.makedirs(os.path.join(directory, "Apps"))
            app_path = Path(directory) / "Apps" / "tailscale.json"

            with run_collector(
                directory,
                [
                    "https://formulae.brew.sh/api/cask/tailscale.json",
                    "https://formulae.brew.sh/api/cask/tailscale-app.json",
                ],
            ) as output:
                with self.assertRaises(SystemExit) as context:
                    collect_app_info.main()

            self.assertEqual(context.exception.code, 1)
            app_data = json.loads(app_path.read_text(encoding="utf-8"))
            self.assertEqual(app_data["homebrew_cask"], "tailscale")
            self.assertEqual(app_data["version"], "1.80.0")
            self.assertEqual(
                collect_app_info.filename_collisions,
                [
                    {
                        "file_path": os.path.join("Apps", "tailscale.json"),
                        "existing_cask": "tailscale",
                        "incoming_cask": "tailscale-app",
                    }
                ],
            )
            self.assertIn("FILENAME COLLISIONS DETECTED: 1", output.getvalue())

    def test_refused_write_leaves_file_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            os.makedirs(os.path.join(directory, "Apps"))
            app_path = Path(directory) / "Apps" / "tailscale.json"

            with run_collector(directory, ["https://formulae.brew.sh/api/cask/tailscale.json"]):
                collect_app_info.main()

            first_write = app_path.read_bytes()
            self.assertEqual(collect_app_info.filename_collisions, [])

            with run_collector(directory, ["https://formulae.brew.sh/api/cask/tailscale-app.json"]):
                with self.assertRaises(SystemExit) as context:
                    collect_app_info.main()

            self.assertEqual(context.exception.code, 1)
            self.assertEqual(app_path.read_bytes(), first_write)
            self.assertEqual(len(collect_app_info.filename_collisions), 1)

    def test_owning_cask_still_updates_its_file(self):
        with tempfile.TemporaryDirectory() as directory:
            os.makedirs(os.path.join(directory, "Apps"))
            app_path = Path(directory) / "Apps" / "tailscale.json"
            url = "https://formulae.brew.sh/api/cask/tailscale.json"

            with run_collector(directory, [url]):
                collect_app_info.main()

            bumped = dict(CASK_INFO[url], version="1.81.0")
            with patch.dict(CASK_INFO, {url: bumped}):
                with run_collector(directory, [url]):
                    collect_app_info.main()

            app_data = json.loads(app_path.read_text(encoding="utf-8"))
            self.assertEqual(app_data["version"], "1.81.0")
            self.assertEqual(app_data["previous_version"], "1.80.0")
            self.assertEqual(app_data["homebrew_cask"], "tailscale")
            self.assertEqual(collect_app_info.filename_collisions, [])

    def test_file_without_stored_cask_is_updated_normally(self):
        with tempfile.TemporaryDirectory() as directory:
            os.makedirs(os.path.join(directory, "Apps"))
            app_path = self.write_app(
                os.path.join(directory, "Apps"),
                "tailscale.json",
                {"name": "Tailscale", "version": "1.0.0", "homebrew_cask": ""},
            )

            with run_collector(directory, ["https://formulae.brew.sh/api/cask/tailscale-app.json"]):
                collect_app_info.main()

            app_data = json.loads(app_path.read_text(encoding="utf-8"))
            self.assertEqual(app_data["homebrew_cask"], "tailscale-app")
            self.assertEqual(app_data["version"], "1.82.0")
            self.assertEqual(collect_app_info.filename_collisions, [])


TAILSCALE_PAYLOAD = {
    "name": ["Tailscale"],
    "desc": "Mesh VPN",
    "version": "1.80.0",
    "url": "https://example.com/tailscale-1.80.0.dmg",
    "homepage": "https://tailscale.com/",
}


class PrefetchTests(unittest.TestCase):
    def setUp(self):
        collect_app_info.cask_cache.clear()
        del collect_app_info.filename_collisions[:]

    def tearDown(self):
        collect_app_info.cask_cache.clear()
        del collect_app_info.filename_collisions[:]

    def test_prefetch_stores_payload_or_exception_per_url(self):
        good_url = "https://formulae.brew.sh/api/cask/tailscale.json"
        missing_url = "https://formulae.brew.sh/api/cask/removed-app.json"
        session = CountingSession(
            {
                good_url: cask_response(TAILSCALE_PAYLOAD),
                missing_url: cask_response(status_code=404),
            }
        )

        with patch.object(collect_app_info, "cask_session", session):
            with contextlib.redirect_stdout(io.StringIO()):
                cache = collect_app_info.prefetch_cask_data([good_url, missing_url])

        self.assertEqual(cache[good_url], TAILSCALE_PAYLOAD)
        self.assertIsInstance(cache[missing_url], collect_app_info.CaskUnavailableError)
        self.assertEqual(cache[missing_url].cask_token, "removed-app")
        self.assertEqual(sorted(session.requested), sorted([good_url, missing_url]))

    def test_prefetched_payload_is_consumed_without_a_second_fetch(self):
        url = "https://formulae.brew.sh/api/cask/tailscale.json"
        session = CountingSession({url: cask_response(TAILSCALE_PAYLOAD)})

        with patch.object(collect_app_info, "cask_session", session):
            with contextlib.redirect_stdout(io.StringIO()):
                collect_app_info.prefetch_cask_data([url])
            app_info = collect_app_info.get_homebrew_app_info(url)

        self.assertEqual(app_info["name"], "Tailscale")
        self.assertEqual(app_info["version"], "1.80.0")
        self.assertEqual(app_info["homebrew_cask"], "tailscale")
        self.assertEqual(session.requested, [url])

    def test_cache_miss_falls_back_to_a_session_fetch(self):
        url = "https://formulae.brew.sh/api/cask/tailscale.json"
        session = CountingSession({url: cask_response(TAILSCALE_PAYLOAD)})

        with patch.object(collect_app_info, "cask_session", session):
            app_info = collect_app_info.get_homebrew_app_info(url)

        self.assertEqual(session.requested, [url])
        self.assertEqual(app_info["version"], "1.80.0")

    def test_prefetched_404_still_deprecates_through_the_loop(self):
        with tempfile.TemporaryDirectory() as directory:
            apps_folder = os.path.join(directory, "Apps")
            os.makedirs(apps_folder)
            app_path = Path(apps_folder) / "vmware_fusion.json"
            app_path.write_text(
                json.dumps(
                    {
                        "name": "VMware Fusion",
                        "version": "13.6.3",
                        "homebrew_cask": "vmware-fusion",
                    }
                ),
                encoding="utf-8",
            )
            url = "https://formulae.brew.sh/api/cask/vmware-fusion.json"
            session = CountingSession({url: cask_response(status_code=404)})

            with run_collector(directory, [url], session=session):
                collect_app_info.main()

            app_data = json.loads(app_path.read_text(encoding="utf-8"))
            self.assertTrue(app_data["deprecated"])
            self.assertEqual(app_data["deprecation_reason"], "cask removed from Homebrew")
            self.assertEqual(session.requested, [url])

    def test_url_in_two_lists_is_fetched_once(self):
        with tempfile.TemporaryDirectory() as directory:
            os.makedirs(os.path.join(directory, "Apps"))
            url = "https://formulae.brew.sh/api/cask/tailscale.json"
            session = CountingSession({url: cask_response(TAILSCALE_PAYLOAD)})

            with run_collector(directory, [url], session=session):
                with patch.object(collect_app_info, "pkg_urls", [url]):
                    collect_app_info.main()

            self.assertEqual(session.requested, [url])
            app_data = json.loads(
                (Path(directory) / "Apps" / "tailscale.json").read_text(encoding="utf-8")
            )
            # The later list owns the type, which only holds if both loops saw the cask.
            self.assertEqual(app_data["type"], "pkg")
            self.assertEqual(collect_app_info.filename_collisions, [])


class CatalogConsistencyTests(unittest.TestCase):
    def test_supported_catalog_matches_non_deprecated_apps(self):
        apps = {
            path.stem: json.loads(path.read_text(encoding="utf-8"))
            for path in (ROOT / "Apps").glob("*.json")
        }
        supported = json.loads(
            (ROOT / "supported_apps.json").read_text(encoding="utf-8")
        )
        expected = {
            name
            for name, app_data in apps.items()
            if not app_data.get("deprecated")
        }

        self.assertEqual(set(supported), expected)

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        badge = re.search(r"Apps_Available-(\d+)-", readme)
        self.assertIsNotNone(badge)
        self.assertEqual(int(badge.group(1)), len(expected))


if __name__ == "__main__":
    unittest.main()
