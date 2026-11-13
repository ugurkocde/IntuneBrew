"""Synthetic declarative fonts; no downloads, tenant IDs or publication."""
import copy
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '.github/scripts'))
import collect_app_info as c


def cask():
    return {'name': ['Example Fonts (Family)'], 'desc': 'Fixture', 'homepage': 'https://example.invalid',
            'version': '3.5.1', 'url': 'https://example.invalid/fonts.tar.xz', 'sha256': 'a' * 64,
            'artifacts': [{'font': ['ttf/Regular Font.ttf']}, {'font': ['Bold.otf']},
                          {'zap': [{'pkgutil': 'org.example.unrelated'}]}]}


class FontCaskTests(unittest.TestCase):
    def test_nonfont_cli_receipt_is_retained_and_all_vendor_lists_retire_font_fields(self):
        url = 'https://formulae.brew.sh/api/cask/example-font.json'
        lists = ['app_urls', 'homebrew_cask_urls', 'pkg_in_pkg_urls', 'pkg_urls', 'pkg_in_dmg_urls']
        for active in lists:
            with self.subTest(active=active), tempfile.TemporaryDirectory() as root, contextlib.ExitStack() as stack:
                previous_cwd = os.getcwd(); os.chdir(root); stack.callback(os.chdir, previous_cwd)
                for name in lists: stack.enter_context(mock.patch.object(c, name, [url] if name == active else []))
                stack.enter_context(mock.patch.object(c, 'custom_scrapers', []))
                for name in ['prefetch_cask_data', 'update_readme_apps', 'update_readme_with_latest_changes', 'reconcile_vendor_dmg']:
                    stack.enter_context(mock.patch.object(c, name))
                stack.enter_context(mock.patch.object(c, 'discover_missing_bundle_id', return_value=None))
                stack.enter_context(mock.patch.object(c, 'find_bundle_id', return_value='org.example.actual'))
                stack.enter_context(mock.patch.object(c, 'calculate_file_hash', return_value='a' * 64))
                stack.enter_context(mock.patch.object(c.requests, 'get', side_effect=AssertionError('No network')))
                stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                raw = cask(); raw['artifacts'] = [{'pkg': ['Example.pkg']}]
                Path('Apps').mkdir(); entry = Path('Apps/example_fonts_family.json')
                previous = {'name': raw['name'][0], 'version': '3.0', 'url': 'https://example.invalid/old.pkg',
                            'homebrew_cask': 'example-font', 'type': 'app', 'fileName': 'old.pkg',
                            'bundleId': 'com.intunebrew.example_fonts_family',
                            'packageIdentifier': 'com.intunebrew.example_fonts_family'}
                if active != 'app_urls': previous['font_payload'] = {'files': ['old.ttf']}
                entry.write_text(json.dumps(previous))
                with mock.patch.dict(c.cask_cache, {url: raw}): c.main()
                updated = json.loads(entry.read_text())
                self.assertNotIn('font_payload', updated)
                if active == 'app_urls':
                    self.assertEqual(updated['bundleId'], previous['bundleId'])
                    self.assertEqual(updated['packageIdentifier'], previous['packageIdentifier'])
                else:
                    self.assertEqual(updated['bundleId'], 'org.example.actual')
                    self.assertNotIn('packageIdentifier', updated)

    def test_collection_refreshes_or_removes_owned_manifest_on_existing_entry(self):
        url = 'https://formulae.brew.sh/api/cask/example-font.json'
        previous_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as root, contextlib.ExitStack() as stack:
            os.chdir(root); stack.callback(os.chdir, previous_cwd)
            for name in ['homebrew_cask_urls', 'pkg_in_pkg_urls', 'pkg_urls', 'pkg_in_dmg_urls', 'custom_scrapers']:
                stack.enter_context(mock.patch.object(c, name, []))
            stack.enter_context(mock.patch.object(c, 'app_urls', [url]))
            for name in ['prefetch_cask_data', 'update_readme_apps', 'update_readme_with_latest_changes']:
                stack.enter_context(mock.patch.object(c, name))
            stack.enter_context(mock.patch.object(c.requests, 'get', side_effect=AssertionError('No network')))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            Path('Apps').mkdir()
            entry = Path('Apps/example_fonts_family.json')
            prior = {'name': 'Example Fonts (Family)', 'version': '3.0', 'type': 'app', 'homebrew_cask': 'example-font',
                     'url': 'https://example.invalid/old.pkg', 'fileName': 'old.pkg', 'bundleId': 'org.example.old',
                     'font_payload': {'source_url': 'old', 'files': ['old.ttf'], 'archive_sha256': 'b' * 64}}
            entry.write_text(json.dumps(prior)); raw = cask()
            with mock.patch.dict(c.cask_cache, {url: raw}): c.main()
            updated = json.loads(entry.read_text())
            self.assertEqual(updated['font_payload'], c.font_only_payload(raw))
            self.assertEqual(updated['bundleId'], 'com.intunebrew.example_fonts_family')
            raw['artifacts'].append({'app': ['Example.app']}); raw['version'] = '4.0'
            with mock.patch.dict(c.cask_cache, {url: raw}): c.main()
            changed = json.loads(entry.read_text())
            self.assertNotIn('font_payload', changed)
            self.assertNotIn('bundleId', changed)
            entry.write_text(json.dumps(updated))
            with mock.patch.object(c, 'app_urls', []), mock.patch.object(c, 'homebrew_cask_urls', [url]), \
                 mock.patch.object(c, 'find_bundle_id', return_value='org.example.actual'), \
                 mock.patch.object(c, 'discover_missing_bundle_id', return_value=None), \
                 mock.patch.object(c, 'reconcile_vendor_dmg'), mock.patch.dict(c.cask_cache, {url: raw}):
                c.main()
            moved = json.loads(entry.read_text())
            self.assertNotIn('font_payload', moved)
            self.assertEqual(moved['bundleId'], 'org.example.actual')

    def test_manifest_is_data_only_and_receipt_overrides_zap(self):
        raw = cask()
        expected = {'source_url': raw['url'], 'archive_sha256': raw['sha256'],
                    'files': ['ttf/Regular Font.ttf', 'Bold.otf']}
        self.assertEqual(c.font_only_payload(raw), expected)
        self.assertEqual(raw, cask())
        with mock.patch.dict(c.cask_cache, {'https://formulae.brew.sh/api/cask/example-font.json': raw}), \
             mock.patch.object(c, 'find_bundle_id', return_value='org.example.unrelated'):
            app = c.get_homebrew_app_info('https://formulae.brew.sh/api/cask/example-font.json', needs_packaging=True)
        self.assertEqual(app['bundleId'], 'com.intunebrew.example_fonts_family')
        self.assertEqual(app['font_payload'], expected)
        self.assertEqual(app['type'], 'app')
        self.assertNotIn('sha', app)

    def test_no_fonts_and_mixed_recipes_keep_existing_path(self):
        self.assertIsNone(c.font_only_payload({'artifacts': []}))
        for key in ['app', 'pkg', 'installer', 'binary', 'suite', 'preflight', 'postflight', 'uninstall', 'artifact']:
            raw = cask(); raw['artifacts'].append({key: ['other']})
            self.assertIsNone(c.font_only_payload(raw), key)

    def test_api_generated_default_target_is_compared_as_literal_data(self):
        raw = cask()
        for artifact in raw['artifacts']:
            if 'font' in artifact:
                artifact['target'] = '/$HOME/Library/Fonts/' + artifact['font'][0].rsplit('/', 1)[-1]
        self.assertEqual(c.font_only_payload(raw)['files'], ['ttf/Regular Font.ttf', 'Bold.otf'])
        for target in ['/Library/Fonts/renamed.ttf', {'target': 'other.ttf'}, '/$HOME/Library/Fonts/other.ttf']:
            broken = copy.deepcopy(raw); broken['artifacts'][0]['target'] = target
            with self.subTest(target=target), self.assertRaises(ValueError): c.font_only_payload(broken)

    def test_invalid_font_declarations_are_held(self):
        paths = ['../x.ttf', '/x.ttf', '.hidden.ttf', 'a/../x.ttf', 'a\\x.ttf', 'a\nx.ttf',
                 'a//x.ttf', 'x.ttc', 'x.otc', 'x.dfont', 'x.txt', 'a/' * 8 + 'x.ttf', 'a' * 129 + '.ttf']
        for path in paths:
            raw = cask(); raw['artifacts'] = [{'font': [path]}]
            with self.subTest(path=path), self.assertRaises(ValueError): c.font_only_payload(raw)
        for fonts in [[{'font': ['x.ttf', {'target': 'x.ttf'}]}], [{'font': 'x.ttf'}],
                      [{'font': ['a/x.ttf']}, {'font': ['b/X.ttf']}],
                      [{'font': [f'x{i}.ttf']} for i in range(257)]]:
            raw = cask(); raw['artifacts'] = fonts
            with self.subTest(fonts=fonts[:2]), self.assertRaises(ValueError): c.font_only_payload(raw)

    def test_invalid_binding_and_unsupported_cask_features_are_held(self):
        changes = [{'sha256': 'no_check'}, {'sha256': 'A' * 64}, {'version': '3,1'}, {'version': '../1'},
                   {'name': ['é']}, {'variations': {'arm64': {}}}, {'container': {'type': 'naked'}},
                   {'url_specs': {'user_agent': 'x'}}, {'url_specs': []}, {'url': 'http://example.invalid/a.zip'},
                   {'url': 'https://user:password@example.invalid/a.zip'}, {'url': 'https://example.invalid/a.zip#x'},
                   {'url': 'https://example.invalid/a.dmg'}, {'url': 'https://example.invalid/a\n.zip'}]
        for change in changes:
            raw = cask(); raw.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError): c.font_only_payload(raw)


if __name__ == '__main__': unittest.main()
