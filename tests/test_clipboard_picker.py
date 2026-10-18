"""Check the Fuzzel clipboard path without a display or real clipboard."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ClipboardPickerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='clipboard-picker-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        bin_dir = self.root / 'bin'
        bin_dir.mkdir()
        self.env = {**os.environ, 'HOME': str(self.root),
                    'PATH': str(bin_dir) + ':' + os.environ['PATH'],
                    'TEST_ROOT': str(self.root), 'FAKE_STATUS': '0',
                    'XDG_CACHE_HOME': str(self.root / 'cache with spaces')}
        scripts = {
            'cliphist': '''import os, sys
from pathlib import Path
root=Path(os.environ['TEST_ROOT'])
if sys.argv[1] == 'list':
    print('7\\t[[ binary data ]]')
else:
    assert sys.stdin.read() == '7\\t[[ binary data ]]\\n'
    (root/'decoded').write_text('yes')
    sys.stdout.buffer.write(b'\\x89PNG\\x00binary\\xff')
''',
            'fuzzel': '''import json, os, sys
from pathlib import Path
root=Path(os.environ['TEST_ROOT'])
(root/'arguments').write_text(json.dumps(sys.argv[1:]))
assert sys.stdin.read() == '7 - [[ binary data ]]\\n'
if int(os.environ['FAKE_STATUS']) == 0:
    print('7 - [[ binary data ]]')
sys.exit(int(os.environ['FAKE_STATUS']))
''',
            'wl-copy': '''import os, sys
from pathlib import Path
(Path(os.environ['TEST_ROOT'])/'clipboard').write_bytes(sys.stdin.buffer.read())
''',
        }
        for name, content in scripts.items():
            path = bin_dir / name
            path.write_text('#!/usr/bin/env python3\n' + content)
            path.chmod(0o755)

    def invoke(self):
        return subprocess.run(['sh', str(ROOT / 'home/.local/bin/clipboard-picker')],
                              env=self.env, capture_output=True, timeout=5)

    def test_binary_content_and_dedicated_history(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root/'clipboard').read_bytes(), b'\x89PNG\x00binary\xff')
        arguments = json.loads((self.root/'arguments').read_text())
        self.assertEqual(arguments, ['--dmenu', '--only-match',
                         '--cache=' + str(self.root/'cache with spaces/fuzzel-menus/clipboard')])

    def test_cancel_does_not_decode_or_replace_clipboard(self):
        self.env['FAKE_STATUS'] = '1'
        self.assertEqual(self.invoke().returncode, 1)
        self.assertFalse((self.root/'decoded').exists())
        self.assertFalse((self.root/'clipboard').exists())
