"""Check picker integration without a display, network, or real clipboard."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'home/.config/tofi/scripts/emoji-picker.sh'


class EmojiPickerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='emoji-picker-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.db = self.root / 'db'
        self.db.mkdir()
        (self.db / 'emojis.txt').write_text('😀 grinning face\n👩🏽‍💻 woman technologist\n')
        self.env = {**os.environ, 'HOME': str(self.root), 'PATH': str(self.bin) + ':' + os.environ['PATH'],
                    'XDG_CACHE_HOME': str(self.root / 'cache with spaces'),
                    'BEMOJI_DB_LOCATION': str(self.db), 'BEMOJI_PICKER': 'tofi',
                    'PICKER_LOG': str(self.root / 'picker.json'),
                    'FAKE_RESULT': '👩🏽‍💻 woman technologist', 'FAKE_STATUS': '0'}
        self.env.pop('BEMOJI_FUZZEL_CACHE', None)
        self.env.pop('BEMOJI_CUSTOM_LIST', None)
        for picker in ('fuzzel', 'tofi'):
            path = self.bin / picker
            path.write_text('#!/usr/bin/env python3\nimport json, os, sys\n'
                            'from pathlib import Path\n'
                            'Path(os.environ["PICKER_LOG"]).write_text(json.dumps({"name": Path(sys.argv[0]).name, '
                            '"args": sys.argv[1:], "input": sys.stdin.read()}))\n'
                            'sys.stdout.write(os.environ["FAKE_RESULT"])\n'
                            'sys.exit(int(os.environ["FAKE_STATUS"]))\n')
            path.chmod(0o755)

    def invoke(self, *args):
        return subprocess.run(['sh', str(SCRIPT), '-e', *args], env=self.env,
                              capture_output=True, text=True, timeout=5)

    def test_fuzzel_uses_private_emoji_cache_and_preserves_combined_emoji(self):
        result = self.invoke('--picker', 'fuzzel')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '👩🏽‍💻')
        log = json.loads((self.root / 'picker.json').read_text())
        self.assertEqual(log['args'], ['--dmenu', '--only-match',
                         '--cache=' + str(self.root / 'cache with spaces/bemoji/fuzzel-history')])
        self.assertIn('😀 grinning face', log['input'])
        self.assertEqual((self.root / 'cache with spaces/bemoji').stat().st_mode & 0o777, 0o700)

    def test_default_stays_tofi(self):
        self.assertEqual(self.invoke().returncode, 0)
        self.assertEqual(json.loads((self.root / 'picker.json').read_text())['name'], 'tofi')
        self.assertFalse((self.root / 'cache with spaces').exists())

    def test_cache_override_is_one_argument(self):
        self.env['BEMOJI_FUZZEL_CACHE'] = str(self.root / 'custom state/emoji counts')
        self.assertEqual(self.invoke('--picker', 'fuzzel').returncode, 0)
        args = json.loads((self.root / 'picker.json').read_text())['args']
        self.assertEqual(args[-1], '--cache=' + self.env['BEMOJI_FUZZEL_CACHE'])

    def test_cancel_produces_no_selection(self):
        self.env.update(FAKE_RESULT='', FAKE_STATUS='1')
        result = self.invoke('--picker', 'fuzzel')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, '')

    def test_picker_argument_validation(self):
        for args in [('--picker',), ('--picker', 'unknown')]:
            self.assertNotEqual(self.invoke(*args).returncode, 0)
            self.assertFalse((self.root / 'picker.json').exists())
