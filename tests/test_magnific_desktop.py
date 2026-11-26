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

    def test_collect_writes_verified_signed_metadata_and_tracks_previous_version(self):
        with tempfile.TemporaryDirectory() as root:
            calls = []

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
                self.spec, apps_folder=root, inspect=fake_inspect
            )
            self.assertEqual(
                calls,
                [(self.spec.url, "com.freepik.magnific.desktop", "CCAL5Z426N")],
            )
            self.assertEqual(first["version"], "1.5.7")
            self.assertEqual(first["previous_version"], "1.5.7")
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
                self.spec, apps_folder=root, inspect=fake_upgrade
            )
            self.assertEqual(second["version"], "1.6.0")
            self.assertEqual(second["previous_version"], "1.5.7")
            saved = json.loads((Path(root) / "magnific_desktop.json").read_text())
            self.assertEqual(saved["version"], "1.6.0")
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
                    self.spec, apps_folder=root, inspect=fake_refusal
                )
            self.assertEqual(json.loads(target.read_text()), original)

    def test_missing_or_whitespace_padded_version_refused(self):
        with tempfile.TemporaryDirectory() as root:
            for bad_version in ("", " ", "1.5.7 ", " 1.5.7"):
                def fake_bad_version(url, bundle_id, *, team_id=None, _v=bad_version):
                    return collect.SignedBundleObservation(
                        artifact_sha256="a" * 64,
                        bundle_id=bundle_id,
                        short_version=_v,
                        bundle_version=_v,
                        team_id=team_id,
                    )

                with self.assertRaisesRegex(ValueError, "invalid version"):
                    collect.collect_direct_vendor_dmg(
                        self.spec, apps_folder=root, inspect=fake_bad_version
                    )
            self.assertFalse((Path(root) / "magnific_desktop.json").exists())

    def test_deadline_exceeded_converted_to_value_error(self):
        with tempfile.TemporaryDirectory() as root:
            def fake_slow(url, bundle_id, *, team_id=None):
                raise collect._StableReleaseDeadline()

            with self.assertRaisesRegex(ValueError, "aborted"):
                collect.collect_direct_vendor_dmg(
                    self.spec, apps_folder=root, inspect=fake_slow
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
            real_replace = os.replace

            def fail_replace(src, dst):
                seen_temps.append(src)
                raise OSError("simulated replace failure")

            with mock.patch.object(os, "replace", side_effect=fail_replace):
                with self.assertRaises(OSError):
                    collect.collect_direct_vendor_dmg(
                        self.spec, apps_folder=root, inspect=fake_inspect
                    )
            self.assertEqual(len(seen_temps), 1)
            self.assertNotEqual(seen_temps[0], f"{target}.tmp")
            self.assertFalse(Path(seen_temps[0]).exists())
            self.assertEqual(json.loads(target.read_text()), original)


if __name__ == "__main__":
    unittest.main()
