"""Direct odc fixtures prove the metadata sidecar cannot hide during expansion."""
import gzip
import hashlib
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))
from font_payload import read_payload, inspect_component


FONT = b'\x00\x01\x00\x00' + b'fixture font bytes' * 3
EXPECTED = {'Font.ttf': {'size': len(FONT), 'sha256': hashlib.sha256(FONT).hexdigest()}}


def member(name, data=b'', mode=stat.S_IFREG | 0o644, uid=0, gid=0, links=1):
    name = name.encode() + b'\0'
    values = [(0, 6), (1, 6), (mode, 6), (uid, 6), (gid, 6), (links, 6), (0, 6),
              (0, 11), (len(name), 6), (len(data), 11)]
    return b'070707' + ''.join(format(v, '0' + str(w) + 'o') for v, w in values).encode() + name + data


ROOT = member('.', mode=stat.S_IFDIR | 0o755)
FILE = member('./Font.ttf', FONT)
END = member('TRAILER!!!', mode=0)


class FontPayloadTests(unittest.TestCase):
    def parse(self, data, allow=False):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'Payload'; path.write_bytes(gzip.compress(data))
            return read_payload(path, EXPECTED, allow)

    def test_clean_original_and_final_payload(self):
        self.assertEqual(self.parse(ROOT + FILE + END), set())
        self.assertEqual(self.parse(ROOT + FILE + END, True), set())

    def test_original_generated_sidecar_allowed_but_final_sidecar_refused(self):
        raw = ROOT + FILE + member('./._Font.ttf', b'metadata') + END
        self.assertEqual(self.parse(raw, True), {'./._Font.ttf'})
        with self.assertRaises(ValueError): self.parse(raw)

    def test_unexplained_duplicate_missing_or_malformed_entries_hold(self):
        cases = [ROOT + FILE + FILE + END, ROOT + END,
                 ROOT + FILE + member('./Other.ttf', FONT) + END,
                 ROOT + FILE + member('./._Other.ttf', b'metadata') + END,
                 ROOT + member('./Font.ttf', b'wrong byte count') + END,
                 ROOT + member('./Font.ttf', b'Z' * len(FONT)) + END,
                 ROOT + member('./Font.ttf', FONT, mode=stat.S_IFREG | 0o600) + END,
                 ROOT + member('./Font.ttf', FONT, mode=stat.S_IFLNK | 0o644) + END,
                 ROOT + member('./Font.ttf', FONT, links=2) + END,
                 ROOT + member('./Font.ttf', FONT, uid=501) + END,
                 ROOT + member('./Font.ttf', FONT, gid=20) + END,
                 member('.', mode=stat.S_IFDIR | 0o700) + FILE + END,
                 ROOT + FILE, ROOT + FILE + END + b'nonzero',
                 b'070701' + (ROOT + FILE + END)[6:]]
        for case in cases:
            with self.subTest(length=len(case)), self.assertRaises(ValueError): self.parse(case, True)

    def test_only_record_alignment_padding_is_allowed(self):
        raw = ROOT + FILE + END
        self.assertEqual(self.parse(raw + b'\0' * ((-len(raw)) % 512)), set())
        with self.assertRaises(ValueError): self.parse(raw + b'\0' * 512)

    def test_component_bom_and_receipt_counterexamples_hold(self):
        facts = {'Font.ttf': {**EXPECTED['Font.ttf'], 'cksum': 123}}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root / 'Payload').write_bytes(gzip.compress(ROOT + FILE + END))
            (root / 'Bom').write_bytes(b'fixture BOM')
            xml = '<pkg-info identifier="com.intunebrew.fixture" version="1" install-location="/Library/Fonts" auth="root" overwrite-permissions="true" relocatable="false" postinstall-action="none" format-version="2"><payload numberOfFiles="2" installKBytes="1"/></pkg-info>'
            info = root / 'PackageInfo'; info.write_text(xml)
            bom = '.\t40755\t0\t0\t\t\n./Font.ttf\t100644\t0\t0\t' + str(len(FONT)) + '\t123\n'
            full = '.\t40755\t0/0\n./Font.ttf\t100644\t0/0\t' + str(len(FONT)) + '\t123\n'
            def inspect(current=bom):
                with mock.patch('font_payload.subprocess.check_output', side_effect=[current, full]):
                    return inspect_component(root, facts, 'com.intunebrew.fixture', '1')
            inspect()
            for modified in [bom.replace('100644', '100600'), bom.replace('\t123\n', '\t124\n'),
                             bom.replace('\t0\t0\t' + str(len(FONT)), '\t501\t0\t' + str(len(FONT))),
                             bom + bom.splitlines()[-1] + '\n']:
                with self.subTest(bom=modified), self.assertRaises(ValueError): inspect(modified)
            for modified in [xml.replace('numberOfFiles="2"', 'numberOfFiles="3"'),
                             xml.replace('auth="root"', 'auth="none"'),
                             xml.replace('installKBytes="1"', 'installKBytes="0"'),
                             xml.replace('</pkg-info>', '<scripts/></pkg-info>'),
                             xml.replace('version="1"', 'version="2"')]:
                info.write_text(modified)
                with self.subTest(xml=modified), self.assertRaises(ValueError): inspect()
            info.write_text(xml); (root / 'Scripts').mkdir()
            with self.assertRaises(ValueError): inspect()


if __name__ == '__main__': unittest.main()
