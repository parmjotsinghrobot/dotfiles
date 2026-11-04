"""Build-on-start and isolated deployment checks for the memory monitor."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('memory_deploy', ROOT / 'scripts/deploy.py')
deploy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(deploy)


class MemoryMonitorTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('cc'), 'C compiler required')
    def test_deployment_build_cache_rebuild_and_rollback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / 'repo'
            home = root / 'home'
            home.mkdir()
            paths = [p for p in json.loads((ROOT / 'manifest.json').read_text())['paths']
                     if 'low-memory-notify' in p]
            self.assertEqual(len(paths), 4)
            for relative in paths:
                source = ROOT / 'home' / relative
                target = repo / 'home' / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                if source.is_symlink():
                    target.symlink_to(os.readlink(source))
                else:
                    shutil.copy2(source, target)
            (repo / 'manifest.json').write_text(json.dumps({'version': 1, 'paths': paths}))
            with contextlib.redirect_stdout(io.StringIO()):
                run = deploy.deploy(repo, home, True)
                self.assertIsNone(deploy.deploy(repo, home, True))
            enabled = home / '.config/systemd/user/default.target.wants/low-memory-notify.service'
            self.assertEqual(enabled.resolve(), (repo / 'home/.config/systemd/user/low-memory-notify.service').resolve())
            # Use a harmless fixture to exercise the real compiler and launcher
            # without registering pressure monitors or sending notifications.
            source = repo / 'home/.local/share/low-memory-notify/monitor.c'
            source.write_text('#include <stdio.h>\nint main(void) { puts("first"); }\n')
            env = {**os.environ, 'HOME': str(home), 'XDG_CACHE_HOME': str(home / '.cache')}
            launcher = home / '.local/bin/low-memory-notify'
            def launch():
                return subprocess.run([str(launcher)], env=env, check=True,
                                      capture_output=True, text=True, timeout=15).stdout.strip()
            self.assertEqual(launch(), 'first')
            binary = home / '.cache/low-memory-notify/monitor'
            built = binary.stat().st_mtime_ns
            self.assertEqual(launch(), 'first')
            self.assertEqual(binary.stat().st_mtime_ns, built)
            source.write_text('#include <stdio.h>\nint main(void) { puts("updated"); }\n')
            # Explicit timestamp avoids filesystem timestamp granularity races.
            stamp = max(source.stat().st_mtime_ns, built + 1_000_000)
            os.utime(source, ns=(stamp, stamp))
            self.assertEqual(launch(), 'updated')
            source.write_text('invalid C\n')
            stamp = binary.stat().st_mtime_ns + 1_000_000
            os.utime(source, ns=(stamp, stamp))
            result = subprocess.run([str(launcher)], env=env, capture_output=True, timeout=15)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(subprocess.check_output([str(binary)], text=True).strip(), 'updated')
            self.assertEqual(list(binary.parent.glob('build.*')), [])
            with contextlib.redirect_stdout(io.StringIO()):
                deploy.rollback(home, run.name, True)
            self.assertFalse(os.path.lexists(enabled))
            self.assertFalse(os.path.lexists(launcher))
