#!/bin/bash
# Package explicitly supported command-line archives without executing them.
set -euo pipefail
app_name=$1
extracted_dir=$2
version=$3
identifier=$4

# Font recipes are data from the cask, not executable packaging instructions.
package_fonts() {
  python3 -B - "$app_name" "$extracted_dir" "$version" "$identifier" "$(dirname "$0")" <<'FONT_PACKAGE_PY'
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def output(*args):
    return subprocess.check_output(args, text=True)


def build_fonts(app_name, extracted, version, identifier, scripts):
    sys.path.insert(0, str(scripts.parent.parent / 'lib'))
    from font_payload import file_facts, inspect_component
    require(re.fullmatch(r'[a-z0-9_]{1,64}', app_name), 'Invalid font app key')
    entry = scripts.parent.parent / 'Apps' / (app_name + '.json')
    if not entry.exists():
        return
    data = json.loads(entry.read_text())
    if 'font_payload' not in data:
        return  # Preserve unsupported CLI archive behaviour.
    require(data.get('type') == 'app' and data.get('version') == version
            and re.fullmatch(r'[0-9A-Za-z][0-9A-Za-z.+-]{0,63}', version)
            and identifier == 'com.intunebrew.' + app_name
            and data.get('bundleId') == identifier, 'Font recipe identity mismatch')
    payload = data['font_payload']
    require(isinstance(payload, dict) and set(payload) == {'source_url', 'archive_sha256', 'files'},
            'Invalid font manifest fields')
    url, digest, files = payload['source_url'], payload['archive_sha256'], payload['files']
    parsed = urllib.parse.urlsplit(url) if isinstance(url, str) else None
    require(parsed is not None and parsed.scheme == 'https' and parsed.hostname
            and parsed.username is None and parsed.password is None and not parsed.fragment
            and not any(c.isspace() or ord(c) < 32 for c in url)
            and parsed.path.lower().endswith(('.zip', '.tar.xz', '.tar.gz', '.tgz', '.tar.bz2', '.tbz'))
            and isinstance(digest, str) and re.fullmatch(r'[0-9a-f]{64}', digest), 'Invalid font archive binding')
    require(isinstance(files, list) and 1 <= len(files) <= 256, 'Invalid font count')
    for path in files:
        require(isinstance(path, str) and 1 <= len(path.split('/')) <= 8
                and all(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 ._+-]{0,127}', p) for p in path.split('/'))
                and path.lower().endswith(('.ttf', '.otf')), 'Invalid declared font path')
    basenames = [PurePosixPath(p).name for p in files]
    require(len(set(n.casefold() for n in basenames)) == len(files), 'Duplicate flattened font name')
    require(extracted.is_dir() and not extracted.is_symlink(), 'Invalid extraction directory')
    # The caller searches this tree for .app/.pkg after returning. Do not let a
    # vendor installer or an ambiguous archive shadow our verified package.
    for parent, dirs, names in os.walk(extracted, followlinks=False):
        require(not any(n.lower().endswith(('.app', '.pkg', '.mpkg')) for n in dirs + names),
                'Font archive contains an application or installer')
    with tempfile.TemporaryDirectory(prefix='intunebrew-fonts-') as temp:
        root = Path(temp)
        archive = root / 'archive'
        subprocess.run(['bash', str(scripts / 'download_vendor.sh'), url, str(archive)], check=True)
        require(archive.stat().st_size <= 2 * 1024 ** 3, 'Font archive download exceeds size bound')
        hashed = hashlib.sha256()
        with archive.open('rb') as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                hashed.update(chunk)
        require(hashed.hexdigest() == digest, 'Font archive SHA mismatch')
        # Inspect every header before reading any payload. Only declared font
        # bytes are copied; no archive path, symlink, hard link or mode is applied.
        suffix = parsed.path.lower()
        is_zip = suffix.endswith('.zip')
        compression, magic = (('xz', b'\xfd7zXZ\x00') if suffix.endswith('.tar.xz') else
                              ('gz', b'\x1f\x8b') if suffix.endswith(('.tar.gz', '.tgz')) else ('bz2', b'BZh'))
        with archive.open('rb') as source:
            require(source.read(4 if is_zip else len(magic)) == (b'PK\x03\x04' if is_zip else magic),
                    'Font archive format differs from declared URL')
        container = zipfile.ZipFile(archive) if is_zip else tarfile.open(archive, 'r:' + compression)
        with container:
            members = container.infolist() if is_zip else container
            entries, fonts, total = {}, set(), 0
            for count, member in enumerate(members, 1):
                require(count <= 10000, 'Font archive has too many entries')
                name = member.filename if is_zip else member.name
                while name.startswith('./'):
                    name = name[2:]
                name = name.rstrip('/')
                if not name or name == '.':
                    require(member.is_dir() if is_zip else member.isdir(), 'Invalid archive root')
                    continue
                require(not name.startswith('/') and '\\' not in name
                        and all(p not in ('', '.', '..') for p in name.split('/'))
                        and not any(ord(c) < 32 or ord(c) == 127 for c in name), 'Unsafe archive path')
                require(name not in entries, 'Duplicate archive member')
                directory = member.is_dir() if is_zip else member.isdir()
                if is_zip:
                    mode = member.external_attr >> 16
                    require(stat.S_IFMT(mode) in (0, stat.S_IFREG, stat.S_IFDIR), 'Archive link or special file')
                    size = member.file_size
                else:
                    require((member.isdir() or member.isfile()) and not member.issparse(), 'Archive link, sparse or special file')
                    size = member.size
                require(size >= 0, 'Invalid archive size')
                total += size
                require(total <= 2 * 1024 ** 3, 'Font archive exceeds expanded size bound')
                require(not name.lower().endswith(('.app', '.pkg', '.mpkg')), 'Vendor app or package in font archive')
                if name.lower().endswith(('.ttf', '.otf', '.ttc', '.otc', '.dfont')):
                    require(not directory, 'Font path is a directory')
                    fonts.add(name)
                entries[name] = (member, directory, size)
            require(fonts == set(files), 'Archive fonts differ from declared payload')
            # No ancestor of a declared path can be a file (or an alias/link).
            for path in files:
                for ancestor in PurePosixPath(path).parents:
                    if str(ancestor) in entries:
                        require(entries[str(ancestor)][1], 'Non-directory font ancestor')
            stage = root / 'payload'
            stage.mkdir(mode=0o755)
            stage.chmod(0o755)
            for path, basename in zip(files, basenames):
                member, directory, size = entries[path]
                require(not directory and 13 <= size <= 64 * 1024 ** 2, 'Font file size outside bounds')
                stream = container.open(member) if is_zip else container.extractfile(member)
                with stream:
                    magic = stream.read(4)
                    require(magic in (b'\x00\x01\x00\x00', b'OTTO', b'true'), 'Invalid font signature')
                    dest = stage / basename
                    with dest.open('xb') as target:
                        target.write(magic)
                        shutil.copyfileobj(stream, target)
                require(dest.stat().st_size == size and dest.stat().st_nlink == 1, 'Font size/link mismatch')
                dest.chmod(0o644)
        subprocess.run(['xattr', '-cr', str(stage)], check=True)
        package = root / 'fonts.pkg'
        built = subprocess.run(['pkgbuild', '--root', str(stage), '--identifier', identifier, '--version', version,
                                '--install-location', '/Library/Fonts', '--ownership', 'recommended', str(package)],
                               check=True, capture_output=True, text=True)
        # Protected provenance can make pkgbuild print warnings while returning
        # success. Validate all retained fields and bytes instead of ignoring it.
        print('Font pkgbuild permission-warning count: ' + str(built.stderr.count('Permission denied')))
        expected = {'.'} | {'./' + b for b in basenames}
        facts = {b: file_facts(stage / b) for b in basenames}
        expanded = root / 'expanded'
        subprocess.run(['pkgutil', '--expand', str(package), str(expanded)], check=True)
        info, rows = inspect_component(expanded, facts, identifier, version, allow_sidecars=True)
        filelist = root / 'bom-files.txt'
        filelist.write_text('\n'.join(rows) + '\n')
        subprocess.run(['mkbom', '-i', str(filelist), str(expanded / 'Bom')], check=True)
        # Always take this path on CI too, including when the original is clean.
        subprocess.run(['tar', '--format', 'cpio', '--uid', '0', '--gid', '0', '--no-xattrs', '--no-acls',
                        '--no-fflags', '--no-mac-metadata', '-czf', str(expanded / 'Payload'), '-C', str(stage), '.'], check=True)
        payload_info = info.getroot().find('payload')
        # pkgbuild rounds the aggregate byte count, not each tiny file separately.
        kilobytes = (sum(f['size'] for f in facts.values()) + 1023) // 1024
        require(kilobytes <= int(payload_info.get('installKBytes')), 'Font package size estimate grew')
        payload_info.set('numberOfFiles', str(len(expected)))
        payload_info.set('installKBytes', str(kilobytes))
        info.write(expanded / 'PackageInfo', encoding='utf-8', xml_declaration=True)
        normalized = root / 'normalized.pkg'
        subprocess.run(['pkgutil', '--flatten', str(expanded), str(normalized)], check=True)
        verified = root / 'verified'
        subprocess.run(['pkgutil', '--expand', str(normalized), str(verified)], check=True)
        inspect_component(verified, facts, identifier, version)
        require(set(output('pkgutil', '--payload-files', str(normalized)).splitlines()) == expected,
                'Built package payload differs (including resource forks)')
        unpacked = root / 'unpacked'
        subprocess.run(['pkgutil', '--expand-full', str(normalized), str(unpacked)], check=True)
        for name in basenames:
            require(file_facts(unpacked / 'Payload' / name) == facts[name], 'Expanded font bytes differ')
        destination = extracted / (app_name + '_' + version + '.pkg')
        require(not destination.exists() and not destination.is_symlink(), 'Font package output already exists')
        shutil.move(str(normalized), str(destination))


try:
    build_fonts(sys.argv[1], Path(sys.argv[2]), sys.argv[3], sys.argv[4], Path(sys.argv[5]).resolve())
except Exception as error:
    print('Font packaging refused: ' + str(error), file=sys.stderr)
    sys.exit(1)
FONT_PACKAGE_PY
}

case "$app_name" in
  azure_cli)
    python "$(dirname "$0")/package_azure_cli.py" "$version" "$extracted_dir/${app_name}_${version}.pkg"
    exit 0 ;;
  git_gui)
    python "$(dirname "$0")/package_git_gui.py" "$version" "$extracted_dir/${app_name}_${version}.pkg"
    exit 0 ;;
  1password_cli) source_dir=.; binaries=(op) ;;
  github_copilot_cli) source_dir=.; binaries=(copilot) ;;
  codex_cli) source_dir=.; binaries=(bin/codex) ;;
  sentinel) source_dir=.; binaries=(sentinel) ;;
  android_sdk_platformtools) source_dir=platform-tools; binaries=(adb fastboot etc1tool hprof-conv make_f2fs make_f2fs_casefold mke2fs) ;;
  android_sdk_commandline_tools) source_dir=cmdline-tools; binaries=(bin/apkanalyzer bin/avdmanager bin/d8 bin/lint bin/profgen bin/r8 bin/resourceshrinker bin/retrace bin/screenshot2 bin/sdkmanager) ;;
  *) package_fonts; exit 0 ;;
esac
for binary in "${binaries[@]}"; do
  if [ ! -f "$extracted_dir/$source_dir/$binary" ]; then
    echo "Missing expected CLI payload: $binary" >&2
    exit 1
  fi
done
payload=$(mktemp -d)
trap 'rm -rf "$payload"' EXIT
install_dir="/usr/local/lib/intunebrew/$app_name"
mkdir -p "$payload$install_dir" "$payload/usr/local/bin"
ditto "$extracted_dir/$source_dir" "$payload$install_dir"
for binary in "${binaries[@]}"; do
  chmod 755 "$payload$install_dir/$binary"
  ln -s "$install_dir/$binary" "$payload/usr/local/bin/$(basename "$binary")"
done
pkgbuild --root "$payload" --identifier "$identifier" --version "$version" \
  --install-location / "$extracted_dir/${app_name}_${version}.pkg"
