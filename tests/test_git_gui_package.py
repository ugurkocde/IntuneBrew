"""Offline source-integrity and staging guards for the Git GUI recipe."""
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
import subprocess
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('git_gui_package', ROOT / '.github/scripts/package_git_gui.py')
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)


class GitGuiPackageTests(unittest.TestCase):
    def test_preinstall_refuses_foreign_commands_without_modifying_them(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / 'volume'
            foreign = target / 'usr/local/bin/gitk'
            foreign.parent.mkdir(parents=True)
            foreign.write_text('#!/bin/sh\necho existing-gitk\n')
            script = root / 'preinstall'
            script.write_text(recipe.PREINSTALL)
            result = subprocess.run(['/bin/sh', str(script), 'package', 'location', str(target)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(foreign.read_text(), '#!/bin/sh\necho existing-gitk\n')
            self.assertFalse((target / 'usr/local/lib/intunebrew/git_gui').exists())

    def test_source_checksum_mismatch_fails_before_extraction(self):
        response = io.BytesIO(b'untrusted source')
        response.url = 'https://source.example.test/source.tar.gz'
        with tempfile.TemporaryDirectory() as directory, patch.object(recipe, 'urlopen', return_value=response):
            with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                recipe.download(response.url, Path(directory) / 'archive', '0' * 64)

    def test_archive_traversal_and_external_links_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, (name, target) in enumerate([('../outside', None), ('src/link', '../../outside')]):
                archive = root / f'{index}.tar'
                with tarfile.open(archive, 'w') as output:
                    member = tarfile.TarInfo(name)
                    if target:
                        member.type = tarfile.SYMTYPE
                        member.linkname = target
                    output.addfile(member)
                with self.assertRaisesRegex(ValueError, 'Unsafe source archive'):
                    recipe.extract(archive, root / str(index))
                self.assertFalse((root / 'outside').exists())

    def test_internal_convenience_links_are_not_materialized(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / 'source.tar'
            with tarfile.open(archive, 'w') as output:
                member = tarfile.TarInfo('src/file')
                member.size = 4
                output.addfile(member, io.BytesIO(b'data'))
                member = tarfile.TarInfo('src/link')
                member.type = tarfile.SYMTYPE
                member.linkname = 'file'
                output.addfile(member)
            source = recipe.extract(archive, root / 'extracted')
            self.assertEqual((source / 'file').read_bytes(), b'data')
            self.assertFalse((source / 'link').exists())


if __name__ == '__main__':
    unittest.main()
