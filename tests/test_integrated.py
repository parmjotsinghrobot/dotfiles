"""Exercise the actual manifest in a temporary home, without desktop actions."""
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
spec = importlib.util.spec_from_file_location('integrated_deploy', ROOT / 'scripts/deploy.py')
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


class IntegratedDeploymentTests(unittest.TestCase):
    def test_actual_manifest_round_trip(self):
        paths = json.loads((ROOT / 'manifest.json').read_text())['paths']
        self.assertTrue(paths)
        with tempfile.TemporaryDirectory(prefix='dotfiles-integrated-') as directory:
            target = Path(directory) / 'home'
            target.mkdir()
            original = target / '.zshenv'
            original.write_text('original shell environment\n')
            unmanaged = target / '.config/unmanaged/state'
            unmanaged.parent.mkdir(parents=True)
            unmanaged.write_bytes(b'keep unmanaged state\x00')
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertIsNone(deploy.deploy(ROOT, target))
                self.assertEqual(original.read_text(), 'original shell environment\n')
                self.assertFalse((target / deploy.STATE).exists())
                run = deploy.deploy(ROOT, target, True)
                for relative in paths:
                    link = target / relative
                    self.assertTrue(link.is_symlink(), relative)
                    self.assertTrue(link.exists(), relative)
                    self.assertEqual(os.readlink(link), str(ROOT / 'home' / relative))
                self.assertIsNone(deploy.deploy(ROOT, target, True))
                deploy.rollback(target, run.name)
                self.assertTrue(original.is_symlink())
                deploy.rollback(target, run.name, True)
                deploy.rollback(target, run.name, True)
            self.assertEqual(original.read_text(), 'original shell environment\n')
            self.assertFalse(original.is_symlink())
            self.assertEqual(unmanaged.read_bytes(), b'keep unmanaged state\x00')
            for relative in paths:
                if relative != '.zshenv':
                    self.assertFalse(os.path.lexists(target / relative), relative)

    @unittest.skipUnless(shutil.which('zsh'), 'zsh is not installed')
    def test_deployed_shell_resolves_plugin_companions_and_cached_updates(self):
        with tempfile.TemporaryDirectory(prefix='dotfiles-shell-') as directory:
            target = Path(directory) / 'home'
            target.mkdir()
            with contextlib.redirect_stdout(io.StringIO()):
                deploy.deploy(ROOT, target, True)
            stubs = Path(directory) / 'bin'
            stubs.mkdir()
            # These explicit stubs keep optional startup and update commands offline.
            for name, text in {'antidot': '#!/bin/sh\nexit 0\n',
                               'checkupdates': '#!/bin/sh\nexit 2\n'}.items():
                executable = stubs / name
                executable.write_text(text)
                executable.chmod(0o755)
            environment = {**os.environ, 'HOME': str(target),
                           'XDG_CONFIG_HOME': str(target / '.config'),
                           'XDG_CACHE_HOME': str(target / '.cache'),
                           'XDG_DATA_HOME': str(target / '.local/share'),
                           'XDG_STATE_HOME': str(target / '.local/state'),
                           'ZDOTDIR': str(target / '.config/zsh'),
                           'PATH': str(stubs) + os.pathsep + os.environ['PATH']}
            command = ('(( $+functions[_zsh_autosuggest_start] )) || exit 31; '
                       '(( $+functions[_zsh_highlight] )) || exit 32; '
                       '(( $+functions[_zsh_highlight_highlighter_main_paint] )) || exit 33; '
                       'dotfiles-refresh-updates || exit 34; '
                       '[[ $(<"$XDG_CACHE_HOME/zsh/updates") == 0 ]] || exit 35')
            result = subprocess.run(['zsh', '-i', '-c', command], env=environment,
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
