"""Strict inspection of IntuneBrew's script-free, flat font component PKGs."""
import gzip
import hashlib
from pathlib import Path
import stat
import subprocess
import xml.etree.ElementTree as ET

FONT_RECIPE = 'font-pkg-v1'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def file_facts(path):
    metadata = path.lstat()
    require(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1
            and 13 <= metadata.st_size <= 64 * 1024 ** 2, 'Invalid staged font file')
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    checksum, length = subprocess.check_output(['cksum', str(path)], text=True).split()[:2]
    require(int(length) == metadata.st_size, 'Font changed during inspection')
    return {'size': metadata.st_size, 'sha256': digest.hexdigest(), 'cksum': int(checksum)}


def read_payload(path, expected, allow_sidecars=False):
    """Read gzip+odc directly: expand-full silently hides AppleDouble records."""
    wanted = {'.'} | {'./' + name for name in expected}
    sidecars = {'./._' + name for name in expected} if allow_sidecars else set()
    seen, extras, consumed = set(), set(), 0
    with gzip.open(path, 'rb') as source:
        def read(size):
            nonlocal consumed
            value = source.read(size); consumed += len(value)
            require(len(value) == size, 'Truncated font cpio')
            return value
        for _ in range(514):
            header = read(76)
            require(header[:6] == b'070707', 'Font payload must be odc cpio')
            fields, offset = [], 6
            for width in (6, 6, 6, 6, 6, 6, 6, 11, 6, 11):
                part = header[offset:offset + width]; offset += width
                require(all(48 <= c <= 55 for c in part), 'Invalid cpio number')
                fields.append(int(part, 8))
            _, _, mode, uid, gid, links, _, _, name_size, size = fields
            require(1 <= name_size <= 260, 'Invalid cpio name length')
            raw_name = read(name_size)
            require(raw_name[-1:] == b'\0' and b'\0' not in raw_name[:-1], 'Invalid cpio name')
            name = raw_name[:-1].decode('utf-8')
            if name == 'TRAILER!!!':
                require(size == 0 and seen >= wanted, 'Missing font payload entries')
                tail = source.read(513)
                # pkgbuild pads to a 512-byte record; bsdtar emits no padding.
                require(len(tail) in (0, (-consumed) % 512) and not any(tail)
                        and not source.read(1), 'Unexpected trailing cpio data')
                return extras
            require(name not in seen and name in wanted | sidecars, 'Unexpected or duplicate font payload entry')
            seen.add(name)
            require(uid == gid == 0, 'Font payload owner mismatch')
            if name == '.':
                require(mode == stat.S_IFDIR | 0o755 and size == 0, 'Font payload root mismatch')
                continue
            require(mode == stat.S_IFREG | 0o644 and links == 1, 'Font payload type, links or mode mismatch')
            if name in sidecars:
                require(size <= 1024 * 1024, 'Oversized generated font metadata')
                read(size); extras.add(name); continue
            facts = expected[name[2:]]
            require(size == facts['size'], 'Font payload size mismatch')
            digest = hashlib.sha256()
            remaining = size
            while remaining:
                chunk = read(min(remaining, 1024 * 1024)); digest.update(chunk); remaining -= len(chunk)
            require(digest.hexdigest() == facts['sha256'], 'Font payload bytes mismatch')
    raise ValueError('Missing cpio trailer or too many entries')


def inspect_component(root, expected, identifier, version, allow_sidecars=False):
    require({p.name for p in root.iterdir()} == {'Bom', 'PackageInfo', 'Payload'}
            and all(p.is_file() and not p.is_symlink() for p in root.iterdir()), 'Unexpected font component layout')
    extras = read_payload(root / 'Payload', expected, allow_sidecars)
    info = ET.parse(root / 'PackageInfo')
    element = info.getroot()
    attributes = {'identifier': identifier, 'version': version, 'install-location': '/Library/Fonts',
                  'auth': 'root', 'overwrite-permissions': 'true', 'relocatable': 'false',
                  'postinstall-action': 'none', 'format-version': '2'}
    require(element.tag == 'pkg-info' and all(element.get(k) == v for k, v in attributes.items()),
            'Font receipt attributes mismatch')
    children = list(element)
    allowed = {'payload', 'bundle-version', 'upgrade-bundle', 'update-bundle',
               'atomic-update-bundle', 'strict-identifier', 'relocate'}
    require(all(c.tag in allowed and not list(c) for c in children)
            and len({c.tag for c in children}) == len(children)
            and len([c for c in children if c.tag == 'payload']) == 1, 'Unexpected font receipt children or scripts')
    payload = element.find('payload')
    require(payload.get('numberOfFiles') == str(1 + len(expected) + len(extras)), 'Font receipt file count mismatch')
    kilobytes = (sum(v['size'] for v in expected.values()) + 1023) // 1024
    actual_kilobytes = int(payload.get('installKBytes', '-1'))
    require(actual_kilobytes >= kilobytes if allow_sidecars else actual_kilobytes == kilobytes,
            'Font receipt size estimate mismatch')
    expected_paths = {'.'} | {'./' + name for name in expected}
    rows = [line.split('\t') for line in subprocess.check_output(
        ['lsbom', '-p', 'fmugsc', str(root / 'Bom')], text=True).splitlines()]
    require(len(rows) == len(expected_paths | extras) and {r[0] for r in rows} == expected_paths | extras,
            'Font BOM inventory mismatch')
    for row in rows:
        name, mode, uid, gid = row[:4]
        require(mode == ('40755' if name == '.' else '100644') and uid == gid == '0', 'Font BOM mode/owner mismatch')
        if name != '.' and name not in extras:
            facts = expected[name[2:]]
            require(len(row) == 6 and row[4:] == [str(facts['size']), str(facts['cksum'])], 'Font BOM size/checksum mismatch')
    full_rows = subprocess.check_output(['lsbom', str(root / 'Bom')], text=True).splitlines()
    require(len(full_rows) == len(rows) and {r.split('\t')[0] for r in full_rows} == expected_paths | extras,
            'Font BOM changed during inspection')
    kept = [row for row in full_rows if row.split('\t')[0] in expected_paths]
    require(len(kept) == len(expected_paths), 'Duplicate font BOM rows')
    return info, kept
