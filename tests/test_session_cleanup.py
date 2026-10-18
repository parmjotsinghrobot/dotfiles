"""Known stale entries only, with isolated homes and no user service operations."""
import contextlib
import fcntl
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('cleanup_legacy', ROOT / 'scripts/cleanup_legacy.py')
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)


class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.capture = contextlib.redirect_stdout(io.StringIO())
        self.capture.__enter__()
        self.addCleanup(self.capture.__exit__, None, None, None)

    def file(self, relative, text):
        path = self.home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def link(self, name, target):
        path = self.home / '.config/systemd/user/default.target.wants' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(target)
        return path

    def test_broken_vs_valid_links_and_unrelated_files(self):
        valid = self.file('installed.service', 'valid')
        stale = self.link('yams.service', '/missing/legacy-yams.service')
        working = self.link('gamemoded.service', valid)
        unrelated = self.link('other.service', '/missing/unrelated.service')
        regular = self.file('.config/systemd/user/default.target.wants/spotblock.service', 'not a symlink')
        matches = cleanup.candidates(self.home)
        self.assertEqual([item[0] for item in matches], [stale.relative_to(self.home)])
        cleanup.cleanup(self.home, True)
        self.assertTrue(working.exists())
        self.assertTrue(unrelated.is_symlink())
        self.assertEqual(regular.read_text(), 'not a symlink')

    def test_dry_run_has_no_writes(self):
        self.link('yams.service', '/missing/yams')
        before = sorted(str(path.relative_to(self.home)) for path in self.home.rglob('*'))
        cleanup.cleanup(self.home)
        after = sorted(str(path.relative_to(self.home)) for path in self.home.rglob('*'))
        self.assertEqual(before, after)
        self.assertFalse((self.home / '.local').exists())

    def test_restore_preserves_dangling_symlink_and_private_storage(self):
        stale = self.link('yams.service', '/missing/yams')
        run = cleanup.cleanup(self.home, True)
        self.assertFalse(os.path.lexists(stale))
        self.assertEqual(run.stat().st_mode & 0o777, 0o700)
        self.assertEqual((run / 'journal.json').stat().st_mode & 0o777, 0o600)
        cleanup.rollback(self.home, run.name)
        self.assertFalse(os.path.lexists(stale))
        cleanup.rollback(self.home, run.name, True)
        self.assertEqual(os.readlink(stale), '/missing/yams')
        cleanup.rollback(self.home, run.name, True)
        self.assertEqual(os.readlink(stale), '/missing/yams')

    def test_regular_file_restore_keeps_content_and_mode(self):
        lunar = self.file('.config/autostart/lunarclient.desktop',
                          'Exec=/tmp/.mount_lunar123/lunarclient --hidden\n')
        lunar.chmod(0o640)
        run = cleanup.cleanup(self.home, True)
        self.assertFalse(lunar.exists())
        cleanup.rollback(self.home, run.name, True)
        self.assertEqual(lunar.read_text(), 'Exec=/tmp/.mount_lunar123/lunarclient --hidden\n')
        self.assertEqual(lunar.stat().st_mode & 0o777, 0o640)

    def test_installed_camera_entrypoint_is_retained(self):
        executable = self.file('python3.14/cameractrlsd.py', '# python entrypoint')
        camera = self.file('.config/systemd/user/cameractrlsd.service',
                           f'ExecStart={executable}\n')
        with patch.object(cleanup, 'CAMERA', executable):
            self.assertEqual(cleanup.candidates(self.home), [])
        self.assertTrue(camera.exists())

    def test_restore_conflict_does_not_overwrite(self):
        stale = self.link('yams.service', '/missing/yams')
        run = cleanup.cleanup(self.home, True)
        stale.write_text('new config')
        with self.assertRaisesRegex(ValueError, 'restore conflict'):
            cleanup.rollback(self.home, run.name, True)
        self.assertEqual(stale.read_text(), 'new config')

    def test_exact_stale_entries_and_replacements(self):
        firefox = self.file('.config/systemd/user/firefox-profile@.service',
                            '[Service]\nExecStart=%h/.local/bin/firefox-sync.sh %i\n')
        camera = self.file('.config/systemd/user/cameractrlsd.service',
                           f'[Service]\nExecStart={cleanup.CAMERA}\n')
        lunar = self.file('.config/autostart/lunarclient.desktop', 'Exec=/tmp/.mount_lunar123/lunarclient --hidden\n')
        waybar = self.file('.local/bin/launch-waybar',
                          'CONFIG_FILES="$HOME/.config/waybar/config $HOME/.config/waybar/style.css"\n'
                          'inotifywait -e create,modify $CONFIG_FILES\nkillall waybar\n')
        with patch.object(cleanup, 'CAMERA', self.home / 'missing-python3.14'):
            # The unit no longer references that exact path: must be retained.
            self.assertNotIn(camera.relative_to(self.home), dict(cleanup.candidates(self.home)))
        with patch.object(cleanup, 'CAMERA', Path('/definitely/missing/python3.14/camera.py')):
            camera.write_text(f'ExecStart={cleanup.CAMERA}\n')
            self.assertEqual(len(cleanup.candidates(self.home)), 4)
            self.file('.local/bin/firefox-sync.sh', '#!/bin/sh')
            self.file('.config/waybar/config', '{}')
            lunar.write_text('Exec=/usr/bin/lunarclient --hidden\n')
            camera.write_text('ExecStart=/usr/bin/cameractrlsd\n')
            self.assertEqual(cleanup.candidates(self.home), [])
        self.assertTrue(firefox.exists())
        self.assertTrue(waybar.exists())

    def test_symlinked_parent_rejected_without_writes(self):
        outside = self.home / 'outside'
        outside.mkdir()
        (self.home / '.config').symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'unsafe parent'):
            cleanup.cleanup(self.home, True)
        self.assertEqual(list(outside.iterdir()), [])

    def test_duplicate_notes_exits_before_connecting_to_sway(self):
        runtime = self.home / 'runtime'
        runtime.mkdir()
        lock = os.open(runtime / 'sticky-notes-daemon.lock', os.O_CREAT | os.O_RDWR, 0o600)
        self.addCleanup(os.close, lock)
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Separate interpreter gives an independent descriptor and real flock contention.
        program = '''import runpy, sys, types
stub = types.ModuleType("i3ipc")
def forbidden():
    raise AssertionError("duplicate connected to Sway")
stub.Connection = forbidden
sys.modules["i3ipc"] = stub
runpy.run_path(sys.argv[1], run_name="__main__")
'''
        result = subprocess.run([sys.executable, '-c', program,
                                 str(ROOT / 'home/.local/bin/sticky-notes-daemon.py')],
                                env={**os.environ, 'XDG_RUNTIME_DIR': str(runtime)},
                                text=True, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')


if __name__ == '__main__':
    unittest.main()
