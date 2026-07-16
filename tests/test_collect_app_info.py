import importlib.util
import json
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


class CollectAppInfoTests(unittest.TestCase):
    def test_homebrew_404_is_reported_as_removed_cask(self):
        response = Mock(status_code=404)
        response.raise_for_status.side_effect = collect_app_info.requests.HTTPError(response=response)

        with patch.object(collect_app_info.requests, "get", return_value=response):
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

        with patch.object(collect_app_info.requests, "get", return_value=response):
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

        with patch.object(collect_app_info.requests, "get", return_value=response):
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
