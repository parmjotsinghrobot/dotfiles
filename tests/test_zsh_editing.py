"""Drive the deployed ZLE with real terminal bytes, without executing the buffer."""
import fcntl
import os
from pathlib import Path
import pty
import select
import shutil
import signal
import struct
import tempfile
import termios
import time
import unittest


@unittest.skipUnless(shutil.which('zsh'), 'zsh is not installed')
class ZshEditingTests(unittest.TestCase):
    def test_editing_and_completion_in_a_terminal(self):
        config = Path(__file__).resolve().parents[1] / 'home/.config/zsh'
        for terminal in ('xterm-kitty', 'xterm-256color'):
            with self.subTest(terminal=terminal), tempfile.TemporaryDirectory() as tmp:
                result = Path(tmp) / 'buffer'
                ready = Path(tmp) / 'ready'
                (Path(tmp) / 'completion-target').touch()
                for name in ('Folder 13', 'Report 24 final', '13-prefix',
                             'Other 13', 'Folder 57', 'Other 57'):
                    (Path(tmp) / 'Documents' / name).mkdir(parents=True)
                (Path(tmp) / 'Unique' / 'Folder 13').mkdir(parents=True)
                for name in ('report.pdf', 'assignment.pdf'):
                    (Path(tmp) / 'Documents' / name).touch()
                (Path(tmp) / '.local/share/daily-nonsense').mkdir(parents=True)
                for name in ('share/one/two/deep-target',
                             'share/one/two/three/too-deep',
                             'share/Folder Name/space-target',
                             'share/ambiguous', 'shadow/ambiguous'):
                    (Path(tmp) / '.local' / name).mkdir(parents=True)
                (Path(tmp) / '.local/share/one/two/result.pdf').touch()
                pid, fd = pty.fork()
                if pid == 0:
                    os.chdir(tmp)
                    os.environ.update(HOME=tmp, ZDOTDIR=str(config), TERM=terminal,
                                      XDG_CACHE_HOME=tmp, ZSH_TEST_DIR=tmp)
                    os.execvp('zsh', ['zsh', '-i'])
                try:
                    def wait_for(path):
                        deadline = time.monotonic() + 8
                        while not path.exists():
                            if time.monotonic() > deadline:
                                self.fail(f'zsh did not produce {path.name}')
                            if select.select([fd], [], [], 0.02)[0]:
                                try:
                                    os.read(fd, 65536)
                                except OSError:
                                    self.fail('zsh exited unexpectedly')

                    os.write(fd, (
                        "HISTFILE=$ZSH_TEST_DIR/history; PROMPT='test> '; "
                        "_test_capture() { print -r -- \"$BUFFER\" >| $ZSH_TEST_DIR/buffer; "
                        "BUFFER=; CURSOR=0; }; zle -N _test_capture; "
                        "bindkey '^X^T' _test_capture; "
                        "print -r -- $TMOUT:$+functions[TRAPALRM] >| $ZSH_TEST_DIR/ready\n"
                    ).encode())
                    wait_for(ready)
                    self.assertEqual(ready.read_text().strip(), '0:0')
                    cases = [
                        (b'abc\x1b[H\x1b[3~\x1b[F!', 'bc!'),
                        (b'abc\x1bOH!\x1bOF?', '!abc?'),
                        (b'abc\x1b[1~!\x1b[4~?', '!abc?'),
                        (b'abc\x1b[7~!\x1b[8~?', '!abc?'),
                        (b'abc\x1b[D\x1b[3~', 'ab'),
                        (b'abc\x1bOD\x1b[3~', 'ab'),
                        (b'one two\x1b[1;5D\x1b[3;5~', 'one '),
                        (b'one two\x1b[H\x1b[1;5C!', 'one !two'),
                        (b'ab\x7fC\x08D', 'aD'),
                        (b'echo completion-t\t', 'echo completion-target '),
                        (b'cd Unique/13\t', 'cd Unique/Folder\\ 13/'),
                        (b'cd Documents/24\t', 'cd Documents/Report\\ 24\\ final/'),
                        (b'cd Documents/13\t', 'cd Documents/13-prefix/'),
                        (b'cd Documents/57\t', None),
                        (b'echo Documents/r.pdf\t', 'echo Documents/report.pdf '),
                        (b'echo Documents/a.pdf\t', 'echo Documents/assignment.pdf '),
                        (b'cd ~/.local/shdaily-nonsense' + b'\x1b[D' * 14 + b'\t',
                         'cd ~/.local/share/daily-nonsense/'),
                        (b'cd .locadaily' + b'\x1b[D' * 5 + b'\t',
                         'cd .local/share/daily-nonsense/'),
                        (b'cd ~/.locadaily' + b'\x1b[D' * 5 + b'\t',
                         'cd ~/.local/share/daily-nonsense/'),
                        (b'cd ~/.local/shdaily' + b'\x1b[D' * 5 + b'\t',
                         'cd ~/.local/share/daily-nonsense/'),
                        (b'cd ~/.local/shdeep-target' + b'\x1b[D' * 11 + b'\t',
                         'cd ~/.local/share/one/two/deep-target/'),
                        (b'cd ~/.local/shspace-target' + b'\x1b[D' * 12 + b'\t',
                         'cd ~/.local/share/Folder\\ Name/space-target/'),
                        (b'cat ~/.local/shresult.pdf' + b'\x1b[D' * 10 + b'\t',
                         'cat ~/.local/share/one/two/result.pdf'),
                        (b'cd ~/.local/shtoo-deep' + b'\x1b[D' * 8 + b'\t',
                         'cd ~/.local/shtoo-deep'),
                        (b'cd ~/.local/sh/daily-nonsense' + b'\x1b[D' * 15 + b'\t',
                         'cd ~/.local/share/daily-nonsense/'),
                        (b'cd ~/.local/shambiguous' + b'\x1b[D' * 9 + b'\t',
                         ('cd ~/.local/share/ambiguous/',
                          'cd ~/.local/shadow/ambiguous/')),
                    ]
                    for keys, expected in cases:
                        if result.exists():
                            result.unlink()
                        os.write(fd, keys + b'\x18\x14')
                        wait_for(result)
                        buffer = result.read_text().rstrip('\n')
                        if expected is None:
                            # An ambiguous substring must not pick either directory.
                            self.assertNotIn(buffer, ('cd Documents/Folder\\ 57/',
                                                      'cd Documents/Other\\ 57/'))
                        elif isinstance(expected, tuple):
                            self.assertNotIn(buffer, expected)
                        else:
                            self.assertEqual(buffer, expected, repr(keys))
                    # Exercise resize/redraw and completion across the old alarm interval.
                    for width in (40, 120, 60, 100):
                        fcntl.ioctl(fd, termios.TIOCSWINSZ,
                                    struct.pack('HHHH', 24, width, 0, 0))
                        os.write(fd, b'echo completion-t\t\x15')
                        time.sleep(0.3)
                    time.sleep(1.1)
                    result.unlink()
                    os.write(fd, b'still-alive\x18\x14')
                    wait_for(result)
                    self.assertEqual(result.read_text().strip(), 'still-alive')
                finally:
                    os.kill(pid, signal.SIGKILL)
                    os.waitpid(pid, 0)
                    os.close(fd)


if __name__ == '__main__':
    unittest.main()
