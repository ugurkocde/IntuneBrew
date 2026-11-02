"""Verify the actual expanded universal package, without installing it."""
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def verify(payload):
    base = payload / 'usr/local/lib/intunebrew/git_gui'
    runtime = base / 'runtime'
    info = json.loads((base / 'provenance.json').read_text())
    assert info['recipe'] == 'git-gui-tcltk-v1'
    assert info['tclTkVersion'] == '9.1.0'
    for filename in ['Git-COPYING', 'tcl-license.terms', 'tk-license.terms']:
        assert (base / 'licenses' / filename).stat().st_size > 0
    for filename in ['git-' + info['gitRelease'] + '.tar.xz', 'tcl9.1.0-src.tar.gz', 'tk9.1.0-src.tar.gz', 'package_git_gui.py']:
        assert (base / 'sources' / filename).is_file()
    count = 0
    for path in runtime.rglob('*'):
        if not path.is_file() or path.is_symlink():
            continue
        data = path.read_bytes()
        for forbidden in (b'/opt/homebrew', b'/usr/local/opt', b'/usr/local/Cellar', b'git-gui-package-'):
            assert forbidden not in data, (path, forbidden)
        if 'Mach-O' not in subprocess.check_output(['/usr/bin/file', '-b', str(path)], text=True):
            continue
        count += 1
        assert set(subprocess.check_output(['/usr/bin/lipo', '-archs', str(path)], text=True).split()) == {'arm64', 'x86_64'}
        subprocess.run(['/usr/bin/codesign', '--verify', '--strict', str(path)], check=True)
        dependencies = subprocess.check_output(['/usr/bin/otool', '-L', str(path)], text=True)
        for line in dependencies.splitlines():
            if ' (compatibility version ' in line:
                dependency = line.strip().split(' (', 1)[0]
                assert dependency.startswith(('/usr/lib/', '/System/Library/', '@loader_path/')), dependency
    assert count >= 4
    # Both toolkit libraries must load without Homebrew, even after relocation.
    env = {**os.environ, 'PATH': '/usr/bin:/bin',
           'TCL_LIBRARY': str(runtime / 'lib/tcl9.1'), 'TK_LIBRARY': str(runtime / 'lib/tk9.1')}
    env.pop('TCLLIBPATH', None)
    with tempfile.TemporaryDirectory() as directory:
        script = Path(directory) / 'smoke.tcl'
        result_file = Path(directory) / 'tk-result'
        script.write_text('wm withdraw .\nset result [open [lindex $argv 0] w]\n'
                          'puts $result [package require Tk]\nputs $result [tk windowingsystem]\n'
                          'close $result\nexit\n')
        subprocess.run([str(runtime / 'bin/wish9.1'), str(script), str(result_file)], env=env, check=True, timeout=30)
        assert result_file.read_text().splitlines() == ['9.1.0', 'aqua']
    result = subprocess.check_output([str(payload / 'usr/local/bin/git-gui'), '--version'],
                                     env={**env, 'TCL_LIBRARY': '/invalid', 'TK_LIBRARY': '/invalid', 'TCLLIBPATH': '/invalid'}, text=True)
    assert result.startswith('git-gui version ')
    # Load each real application and its Tcl modules against a private repository.
    # A modal startup failure cannot satisfy the marker and times out instead.
    with tempfile.TemporaryDirectory() as directory:
        repo = Path(directory)
        env.update(GIT_GUI_LIB_DIR=str(base / 'share/git-gui/lib'),
                   GITK_MSGSDIR=str(base / 'share/gitk/lib/msgs'),
                   GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null')
        subprocess.run(['/usr/bin/git', 'init', '-q', str(repo)], check=True, env=env)
        (repo / 'README').write_text('Git GUI package fixture\n')
        subprocess.run(['/usr/bin/git', 'add', 'README'], cwd=repo, env=env, check=True)
        subprocess.run(['/usr/bin/git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                        'commit', '-qm', 'Fixture'], cwd=repo, env=env, check=True)
        # Enter through the actual public wrapper. A Git spy runs a Tcl PATH
        # probe from inside the environment exported by that wrapper, then
        # delegates all Git operations to the real system Git.
        spy = repo / 'spy-bin'
        spy.mkdir()
        probe = repo / 'discovery.tcl'
        probe.write_text('set destination [lindex $argv 0]\n'
                         'set temporary "$destination.[pid].tmp"\n'
                         'set result [open $temporary w]\n'
                         'puts $result [file normalize [lindex [auto_execok gitk] 0]]\n'
                         'close $result\nfile rename -force $temporary $destination\n')
        discovery = repo / 'discovered-gitk'
        git = spy / 'git'
        git.write_text('#!/bin/sh\nset -eu\n'
                       '"$GITGUI_PROBE_TCLSH" "$GITGUI_PROBE_SCRIPT" "$GITGUI_PROBE_RESULT"\n'
                       'exec /usr/bin/git "$@"\n')
        git.chmod(0o755)
        probe_env = {**env, 'PATH': str(spy) + ':' + str(payload / 'usr/local/bin') + ':/usr/bin:/bin',
                     'GITGUI_PROBE_TCLSH': str(runtime / 'bin/tclsh9.1'),
                     'GITGUI_PROBE_SCRIPT': str(probe), 'GITGUI_PROBE_RESULT': str(discovery),
                     'TCL_LIBRARY': '/invalid', 'TK_LIBRARY': '/invalid', 'TCLLIBPATH': '/invalid'}
        process = subprocess.Popen([str(payload / 'usr/local/bin/git-gui')], cwd=repo,
                                   env=probe_env, start_new_session=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 30
            while process.poll() is None and time.monotonic() < deadline:
                if discovery.is_file() and discovery.stat().st_size > 0:
                    break
                time.sleep(0.2)
        finally:
            if process.poll() is None:
                # Terminate only this test's application/process group.
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
            process.communicate(timeout=10)
        assert discovery.is_file(), 'Public Git GUI wrapper never reached Git discovery'
        assert Path(discovery.read_text().strip()).resolve() == (base / 'bin/gitk').resolve(), discovery.read_text()
        for command in ('git-gui', 'gitk'):
            script = repo / 'application-smoke.tcl'
            result_file = repo / (command + '-result')
            script.write_text('set result_path [lindex $argv 0]\n'
                              'set argv0 {' + str(base / 'bin' / command) + '}\n'
                              'set argv {}\nset argc 0\n'
                              'if {[catch {source $argv0} problem]} {puts stderr $problem; exit 1}\n'
                              'wm withdraw .\n'
                              'if {[llength [winfo children .]] < 2} {exit 1}\n'
                              'set result [open $result_path w]\nputs $result APPLICATION_READY\n'
                              'close $result\nafter 100 {destroy .; exit 0}\n')
            subprocess.run([str(runtime / 'bin/wish9.1'), str(script), str(result_file)],
                           cwd=repo, env=env, check=True, timeout=30)
            assert result_file.read_text().strip() == 'APPLICATION_READY', command
    print('Universal signed Tcl/Tk, Aqua runtime, source archives, licenses and Git GUI command verified')


if __name__ == '__main__':
    verify(Path(sys.argv[1]).resolve())
