"""Verify the GUI launch path from a session lacking the Qt variable."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gui_deploy', ROOT/'scripts/deploy.py')
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


class GuiEnvironmentTests(unittest.TestCase):
    def test_deployed_gui_launcher_sets_qt_default_and_preserves_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)/'home'
            home.mkdir()
            with contextlib.redirect_stdout(io.StringIO()):
                deploy.deploy(ROOT, home, True)
            env = {**os.environ, 'HOME': str(home), 'XDG_CONFIG_HOME': str(home/'.config')}
            env.pop('QT_QPA_PLATFORMTHEME', None)
            result = subprocess.run([str(home/'.local/bin/launch-app'), 'python3', '-c',
                'import json,os,sys;print(json.dumps([os.environ.get("QT_QPA_PLATFORMTHEME"),sys.argv[1:]]))',
                'argument with spaces', '$(not-a-shell-command)'], env=env,
                capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(result.stdout), ['qt5ct', ['argument with spaces', '$(not-a-shell-command)']])

    def test_shell_defaults_preserve_explicit_override(self):
        result = subprocess.run(['sh', '-c', '. "$1"; printf "%s" "$QT_QPA_PLATFORMTHEME"',
            'sh', str(ROOT/'home/.config/shell/environment.sh')],
            env={**os.environ, 'QT_QPA_PLATFORMTHEME': 'custom-app-theme'},
            capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout, 'custom-app-theme')
