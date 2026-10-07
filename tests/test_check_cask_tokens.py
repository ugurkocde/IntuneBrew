import ast
import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_cask_tokens", ROOT / ".github/scripts/check_cask_tokens.py"
)
check_cask_tokens = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_cask_tokens)

RECIPE_SPEC = importlib.util.spec_from_file_location(
    "request_sources", ROOT / ".github/scripts/request_sources.py"
)
request_sources = importlib.util.module_from_spec(RECIPE_SPEC)
RECIPE_SPEC.loader.exec_module(request_sources)


class CaskTokenHealthTests(unittest.TestCase):
    def run_check(self, index, deprecated=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "collector.py"
            source.write_text(
                'sources = ["https://formulae.brew.sh/api/cask/example.json"]\n'
            )
            apps = root / "Apps"
            apps.mkdir()
            (apps / "example.json").write_text(json.dumps({
                "name": "Example", "version": "1.0",
                "homebrew_cask": "example", "deprecated": deprecated,
            }))
            output = root / "output"
            report = root / "report.md"
            with (
                patch.object(check_cask_tokens, "SCRIPT_FILE", str(source)),
                patch.object(check_cask_tokens, "APPS_FOLDER", str(apps)),
                patch.object(check_cask_tokens, "REPORT_FILE", str(report)),
                patch.object(check_cask_tokens, "fetch_cask_index", return_value=index),
                patch.dict(os.environ, {"GITHUB_OUTPUT": str(output)}),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                status = check_cask_tokens.main()
            return status, output.read_text() if output.exists() else "", report.read_text()

    def test_unavailable_or_invalid_index_cannot_report_recovery(self):
        for index in (None, [], {}, [None], [{}], [{"token": ""}], [{"token": 123}]):
            with self.subTest(index=index):
                status, output, report = self.run_check(index)
                self.assertNotEqual(status, 0)
                self.assertNotIn("missing_count", output)
                self.assertIn("check skipped", report)

    def test_complete_index_reports_recovery(self):
        status, output, report = self.run_check([{"token": "example"}])
        self.assertEqual(status, 0)
        self.assertEqual(output, "missing_count=0\n")
        self.assertIn("Every referenced cask still exists", report)

    def test_missing_deprecated_source_is_still_reported(self):
        status, output, report = self.run_check([{"token": "other"}], deprecated=True)
        self.assertEqual(status, 0)
        self.assertEqual(output, "missing_count=1\n")
        self.assertIn("Example (deprecated)", report)
        self.assertIn("0 of which back an app that is still live", report)

    def test_all_collector_cask_lists_are_covered(self):
        source = ROOT / check_cask_tokens.SCRIPT_FILE
        list_names = {
            "app_urls", "homebrew_cask_urls", "pkg_urls",
            "pkg_in_pkg_urls", "pkg_in_dmg_urls",
        }
        urls = []
        found = set()
        for node in ast.parse(source.read_text()).body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in list_names:
                        found.add(target.id)
                        urls.extend(ast.literal_eval(node.value))
        self.assertEqual(found, list_names)
        expected = {
            urlparse(url).path.rsplit("/", 1)[1].removesuffix(".json")
            for url in urls if urlparse(url).path.startswith("/api/cask/")
        }
        self.assertEqual(set(check_cask_tokens.referenced_tokens(source)), expected)
        self.assertNotIn("azure-cli", expected)  # A formula, not a cask.

    def test_configured_formulas_have_supported_packaging_recipes(self):
        """Reject formula sources the collector cannot turn into catalog apps."""
        list_names = {
            "app_urls", "homebrew_cask_urls", "pkg_urls",
            "pkg_in_pkg_urls", "pkg_in_dmg_urls",
        }
        found = set()
        formulas = set()
        source = ROOT / check_cask_tokens.SCRIPT_FILE
        for node in ast.parse(source.read_text()).body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in list_names:
                        found.add(target.id)
                        for url in ast.literal_eval(node.value):
                            path = urlparse(url).path
                            if path.startswith("/api/formula/"):
                                formulas.add(path.rsplit("/", 1)[1].removesuffix(".json"))
        self.assertEqual(found, list_names)
        for token in formulas:
            with self.subTest(formula=token):
                self.assertIn(token, request_sources.FORMULA_RECIPES)
        self.assertNotIn("antigen", formulas)
        self.assertIn("azure-cli", formulas)
        self.assertEqual(request_sources.FORMULA_RECIPES["azure-cli"], "azure-cli-universal-v1")

    def test_retired_swifty_source_is_removed_but_history_is_retained(self):
        tokens = check_cask_tokens.referenced_tokens(ROOT / check_cask_tokens.SCRIPT_FILE)
        self.assertNotIn("swifty", tokens)
        historical = json.loads((ROOT / "Apps/swifty.json").read_text())
        self.assertTrue(historical["deprecated"])
        self.assertEqual(historical["homebrew_cask"], "swifty")


if __name__ == "__main__":
    unittest.main()
