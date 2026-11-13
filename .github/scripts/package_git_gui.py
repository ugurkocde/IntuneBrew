"""Package Git GUI with a pinned universal Tcl/Tk runtime, without Homebrew."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tarfile
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

RECIPE = "git-gui-tcltk-v1"
TCLTK_VERSION = "9.1.0"
TCLTK_SHA256 = {
    "tcl": "536c45543f64d6eb11832d97ba3494aacff046fbc5040273bd55258d0e448ff1",
    "tk": "772ce7a97c07c2db4c957c93af7ab4dff4bd3037772836b6afbcd0974023b3d6",
}
PREFIX = Path("/usr/local/lib/intunebrew/git_gui")
COMMANDS = ("git-gui", "git-citool", "gitk")
PREINSTALL = '''#!/bin/sh
set -eu
target=${3:-/}
for command in git-gui git-citool gitk; do
  path="$target/usr/local/bin/$command"
  if [ -e "$path" ] || [ -L "$path" ]; then
    if [ -L "$path" ] || ! /usr/bin/grep -Fq '../lib/intunebrew/git_gui' "$path"; then
      echo "Refusing to replace an existing $command from another installation" >&2
      exit 1
    fi
  fi
done
if [ -e "$target/usr/local/lib/intunebrew/git_gui" ]; then
  /usr/sbin/pkgutil --volume "$target" --pkg-info com.intunebrew.git_gui >/dev/null
fi
'''


def download(url, destination, checksum=None):
    if not url.startswith("https://"):
        raise ValueError("Source download must use HTTPS")
    retryable = (TimeoutError, ConnectionResetError, socket.timeout)
    network_errors = (URLError,) + retryable
    for attempt in range(2):
        network_error = None
        try:
            response = urlopen(url, timeout=60)
        except network_errors as error:
            network_error = error
        else:
            # Each attempt truncates its private output. Local file operations
            # deliberately stay outside the network exception handlers.
            with response, destination.open("wb") as output:
                if not response.url.startswith("https://"):
                    raise ValueError("Source redirected outside HTTPS")
                total = 0
                while True:
                    try:
                        chunk = response.read(1024 * 1024)
                    except network_errors as error:
                        network_error = error
                        break
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > 100 * 1024 * 1024:
                        raise ValueError("Source exceeds the recipe's download limit")
                    output.write(chunk)
        if network_error is None:
            break
        reason = network_error.reason if isinstance(network_error, URLError) else network_error
        if (isinstance(network_error, HTTPError) or not isinstance(reason, retryable) or attempt == 1):
            raise network_error
        time.sleep(1)
    if checksum and hashlib.sha256(destination.read_bytes()).hexdigest() != checksum:
        raise ValueError("Source SHA-256 mismatch")


def extract(archive, destination):
    """Reject paths, links and special files that escape the private staging area."""
    destination.mkdir()
    with tarfile.open(archive) as source:
        members = source.getmembers()
        if sum(m.size for m in members) > 500 * 1024 * 1024:
            raise ValueError("Expanded source exceeds the recipe's limit")
        for member in members:
            path = destination / member.name
            if not path.resolve().is_relative_to(destination.resolve()):
                raise ValueError("Unsafe source archive path")
            if member.issym() or member.islnk():
                target = path.parent / member.linkname if member.issym() else destination / member.linkname
                if not target.resolve().is_relative_to(destination.resolve()):
                    raise ValueError("Unsafe source archive link")
                # Git's source archive has convenience links outside the two
                # subprojects we build. Do not materialize any archive links.
                continue
            if not (member.isfile() or member.isdir()):
                raise ValueError("Source archive contains a link or special file")
        source.extractall(destination, members=[m for m in members if m.isfile() or m.isdir()])
    directories = list(destination.iterdir())
    if len(directories) != 1 or not directories[0].is_dir():
        raise ValueError("Expected one source directory")
    return directories[0]


def run(arguments, **kwargs):
    subprocess.run([str(a) for a in arguments], check=True, **kwargs)


def relocate_runtime(runtime):
    binaries = []
    for path in runtime.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        if "Mach-O" not in subprocess.check_output(["/usr/bin/file", "-b", str(path)], text=True):
            continue
        arches = subprocess.check_output(["/usr/bin/lipo", "-archs", str(path)], text=True).split()
        if set(arches) != {"arm64", "x86_64"}:
            raise ValueError("Tcl/Tk runtime is not universal")
        dependencies = subprocess.check_output(["/usr/bin/otool", "-L", str(path)], text=True)
        for line in dependencies.splitlines():
            if " (compatibility version " not in line:
                continue
            dependency = line.strip().split(" (", 1)[0]
            if dependency.startswith(str(PREFIX / "runtime") + "/"):
                target = runtime / Path(dependency).relative_to(PREFIX / "runtime")
                if target == path:
                    run(["/usr/bin/install_name_tool", "-id", "@loader_path/" + path.name, path])
                else:
                    relative = os.path.relpath(target, path.parent)
                    run(["/usr/bin/install_name_tool", "-change", dependency, "@loader_path/" + relative, path])
            elif not dependency.startswith(("/usr/lib/", "/System/Library/", "@loader_path/")):
                raise ValueError("Unexpected external Tcl/Tk library: " + dependency)
        run(["/usr/bin/codesign", "--force", "--sign", "-", path])
        run(["/usr/bin/codesign", "--verify", "--strict", path])
        binaries.append(path)
    if not binaries:
        raise ValueError("Missing Tcl/Tk runtime binaries")


def wrapper(command):
    if command not in COMMANDS:
        raise ValueError("Unexpected Git GUI command")
    return '''#!/bin/sh
set -eu
base="$(CDPATH= cd -- "$(dirname -- "$0")/../lib/intunebrew/git_gui" && pwd)"
unset TCL_LIBRARY TK_LIBRARY TCLLIBPATH
export TCL_LIBRARY="$base/runtime/lib/tcl9.1"
export TK_LIBRARY="$base/runtime/lib/tk9.1"
export GIT_GUI_LIB_DIR="$base/share/git-gui/lib"
export GITK_MSGSDIR="$base/share/gitk/lib/msgs"
export PATH="$base/bin:$base/runtime/bin:$PATH"
exec "$base/bin/COMMAND" "$@"
'''.replace("COMMAND", command)


def build(version, output):
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Expected a Git release version")
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="git-gui-package-") as directory:
        stage = Path(directory)
        metadata_file = stage / "formula.json"
        download("https://formulae.brew.sh/api/formula/git-gui.json", metadata_file)
        metadata = json.loads(metadata_file.read_text())
        if metadata.get("name") != "git-gui" or metadata.get("versions", {}).get("stable") != version:
            raise ValueError("Requested release does not match the current Git GUI formula")
        stable = metadata["urls"]["stable"]
        if not re.fullmatch(r"[a-f0-9]{64}", stable.get("checksum", "")):
            raise ValueError("Missing Git source checksum")
        git_archive = stage / "git.tar.xz"
        download(stable["url"], git_archive, stable["checksum"])
        git_source = extract(git_archive, stage / "git-source")
        payload = stage / "payload"
        base = payload / PREFIX.relative_to("/")
        runtime = base / "runtime"
        sources = base / "sources"
        sources.mkdir(parents=True)
        shutil.copy2(git_archive, sources / ("git-" + version + ".tar.xz"))
        build_env = {**os.environ, "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                     "CC": "/usr/bin/clang", "MACOSX_DEPLOYMENT_TARGET": "11.0",
                     "CFLAGS": "-O2 -arch arm64 -arch x86_64 -mmacosx-version-min=11.0 "
                               + "-ffile-prefix-map=" + str(stage) + "=/usr/src/intunebrew/git_gui",
                     "LDFLAGS": "-arch arm64 -arch x86_64 -mmacosx-version-min=11.0"}
        for key in ("CPATH", "LIBRARY_PATH", "CPPFLAGS", "TCL_LIBRARY", "TK_LIBRARY", "TCLLIBPATH"):
            build_env.pop(key, None)
        licenses = base / "licenses"
        licenses.mkdir()
        shutil.copy2(git_source / "COPYING", licenses / "Git-COPYING")
        for name in ("tcl", "tk"):
            archive = stage / (name + "-src.tar.gz")
            url = f"https://downloads.sourceforge.net/project/tcl/Tcl/{TCLTK_VERSION}/{name}{TCLTK_VERSION}-src.tar.gz"
            download(url, archive, TCLTK_SHA256[name])
            source = extract(archive, stage / (name + "-source"))
            shutil.copy2(archive, sources / (name + TCLTK_VERSION + "-src.tar.gz"))
            shutil.copy2(source / "license.terms", licenses / (name + "-license.terms"))
            work = stage / (name + "-build")
            work.mkdir()
            configure = [source / "unix/configure", "--prefix=" + str(PREFIX / "runtime"),
                         "--enable-shared", "--disable-zipfs"]
            if name == "tk":
                configure += ["--enable-aqua=yes", "--without-x", "--with-tcl=" + str(stage / "tcl-build")]
            run(configure, cwd=work, env=build_env)
            if name == "tcl":
                # Tcl records build-machine fallback paths in its core library.
                # Use installation paths for these two diagnostic/fallback
                # constants; retain the source path used by build-time tools.
                makefile = work / "Makefile"
                lines = makefile.read_text().splitlines(keepends=True)
                changed = 0
                for index, line in enumerate(lines):
                    if "-DTCL_BUILDTIME_SCRDIR=" in line:
                        lines[index] = line.replace("$(TCL_BUILDTIME_LIBRARY)", "$(TCL_LIBRARY)")
                        changed += lines[index] != line
                    elif "-DTCL_BUILDTIME_BINDIR=" in line:
                        lines[index] = line.replace("$(ABS_BUILD_DIR)", "$(bindir)")
                        changed += lines[index] != line
                if changed != 2:
                    raise ValueError("Tcl build-path constants changed upstream")
                makefile.write_text("".join(lines))
            run(["/usr/bin/make", "-j4", "binaries", "libraries"], cwd=work, env=build_env)
            run(["/usr/bin/make", "install-binaries", "install-libraries", "DESTDIR=" + str(payload)], cwd=work, env=build_env)
        relocate_runtime(runtime)
        env = {**build_env, "PATH": str(runtime / "bin") + ":" + build_env["PATH"],
               "TCL_LIBRARY": str(runtime / "lib/tcl9.1"), "TK_LIBRARY": str(runtime / "lib/tk9.1")}
        for subdirectory in ("git-gui", "gitk-git"):
            run(["/usr/bin/make", "install", "prefix=" + str(PREFIX), "gitexecdir=" + str(PREFIX / "bin"),
                 "sharedir=" + str(PREFIX / "share"), "TCLTK_PATH=wish9.1",
                 "TCL_PATH=" + str(runtime / "bin/tclsh9.1"), "TKFRAMEWORK=/dev/null", "NO_MSGFMT=1",
                 "DESTDIR=" + str(payload)], cwd=git_source / subdirectory, env=env)
        # These development files embed build paths and are unnecessary at runtime.
        shutil.rmtree(runtime / "include", ignore_errors=True)
        for pattern in ("*.a", "*Config.sh"):
            for file in runtime.rglob(pattern):
                file.unlink()
        for command in COMMANDS:
            entry = payload / "usr/local/bin" / command
            entry.parent.mkdir(parents=True, exist_ok=True)
            entry.write_text(wrapper(command))
            entry.chmod(0o755)
        provenance = {"recipe": RECIPE, "gitRelease": version, "gitSource": stable,
                      "tclTkVersion": TCLTK_VERSION, "tclTkSha256": TCLTK_SHA256,
                      "requires": "A working git installation (Xcode Command Line Tools or another Git distribution).",
                      "commands": COMMANDS}
        (base / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
        # Include the exact build recipe and complete original source archives.
        shutil.copy2(__file__, sources / "package_git_gui.py")
        (sources / "BUILDING.txt").write_text(
            "Build on macOS with Xcode Command Line Tools and Python 3.9+:\n"
            "python3 package_git_gui.py " + version + " git_gui.pkg\n"
            "The complete unmodified source archives and licenses are included.\n"
            "Git GUI's own --version differs from the containing Git release.\n")
        result = subprocess.check_output([str(payload / "usr/local/bin/git-gui"), "--version"], env=env, text=True)
        if not result.startswith("git-gui version "):
            raise ValueError("Staged Git GUI version check failed")
        scripts = stage / "installer-scripts"
        scripts.mkdir()
        preinstall = scripts / "preinstall"
        preinstall.write_text(PREINSTALL)
        preinstall.chmod(0o755)
        run(["/usr/bin/pkgbuild", "--root", payload, "--scripts", scripts, "--identifier", "com.intunebrew.git_gui",
             "--version", version, "--install-location", "/", output])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build(args.version, args.output)
