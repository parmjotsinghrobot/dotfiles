"""Focused checks for status recovery, volume commands and the coffee toggle."""
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch


STATUS = Path(__file__).resolve().parents[1] / 'home/.config/sway/swaybar/status.py'
SPEC = importlib.util.spec_from_file_location('swaybar_status', STATUS)
status = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(status)
status.load_dbus()


class SwaybarStatusTests(unittest.TestCase):
    def test_volume_commands_keep_steps_limit_and_mute(self):
        commands = {
            'up': ('set-volume', '-l', '1.0', status.DEFAULT_SINK, '5%+'),
            'down': ('set-volume', status.DEFAULT_SINK, '5%-'),
            'mute': ('set-mute', status.DEFAULT_SINK, 'toggle'),
        }
        for action, command in commands.items():
            with self.subTest(action=action), patch.object(status, 'run') as run:
                status.adjust_volume(action)
                run.assert_called_once_with('wpctl', *command)

    def test_output_switch_is_resolved_for_each_read_and_command(self):
        # A stand-in for wpctl resolving its default alias at invocation time.
        active = 'speakers'
        seen = []
        def wpctl(*args):
            if args[1] == 'get-volume':
                self.assertEqual(args[2], status.DEFAULT_SINK)
                return {'speakers': 'Volume: 0.20', 'Bluetooth': 'Volume: 0.65',
                        'USB': 'Volume: 0.40'}[active]
            if args[1] == 'inspect':
                return ''
            self.assertIn(status.DEFAULT_SINK, args)
            seen.append(active)
            return ''
        with patch.object(status, 'run', side_effect=wpctl):
            for active, percent in [('speakers', 20), ('Bluetooth', 65), ('USB', 40)]:
                self.assertTrue(status.volume()[0]['full_text'].endswith(str(percent)))
                status.adjust_volume('up')
        self.assertEqual(seen, ['speakers', 'Bluetooth', 'USB'])

    def test_volume_cli_dispatches_without_starting_status_workers(self):
        for action in ('up', 'down', 'mute'):
            with self.subTest(action=action), patch.object(sys, 'argv', ['status.py', '--volume', action]), \
                    patch.object(status, 'adjust_volume') as adjust, \
                    patch.object(status, 'read_volume', return_value=(45, action == 'mute')), \
                    patch.object(status, 'show_osd') as osd, \
                    patch.object(status.threading, 'Thread') as thread:
                status.main()
                adjust.assert_called_once_with(action)
                osd.assert_called_once_with(45, 'muted' if action == 'mute' else 'volume')
                thread.assert_not_called()

    def test_brightness_commands_keep_five_percent_steps(self):
        for action, step in [('up', '5%+'), ('down', '5%-')]:
            with self.subTest(action=action), patch.object(status, 'run',
                    return_value='intel_backlight,backlight,33600,35%,96000') as run:
                self.assertEqual(status.adjust_brightness(action), 35)
                run.assert_called_once_with('brightnessctl', '--machine-readable', 'set', step)
        with patch.object(status, 'run', return_value='bad response'):
            with self.assertRaises(ValueError):
                status.adjust_brightness('up')

    def test_brightness_cli_reports_result_without_starting_workers(self):
        with patch.object(sys, 'argv', ['status.py', '--brightness', 'down']), \
                patch.object(status, 'adjust_brightness', return_value=35) as adjust, \
                patch.object(status, 'show_osd') as osd, \
                patch.object(status.threading, 'Thread') as thread:
            status.main()
            adjust.assert_called_once_with('down')
            osd.assert_called_once_with(35, 'brightness')
            thread.assert_not_called()

    def test_feedback_failure_does_not_fail_successful_adjustment(self):
        for arguments, error in [(['--volume', 'up'], FileNotFoundError('no FIFO')),
                                 (['--brightness', 'up'], BlockingIOError('full FIFO'))]:
            with self.subTest(arguments=arguments), \
                    patch.object(sys, 'argv', ['status.py', *arguments]), \
                    patch.object(status, 'adjust_volume'), \
                    patch.object(status, 'read_volume', return_value=(35, False)), \
                    patch.object(status, 'adjust_brightness', return_value=35), \
                    patch.object(status, 'show_osd', side_effect=error), \
                    patch.object(sys, 'stderr', io.StringIO()) as errors:
                status.main()
                self.assertIn('osd:', errors.getvalue())

    def test_osd_fifo_protocol_and_nonblocking_missing_reader(self):
        with tempfile.TemporaryDirectory() as runtime, \
                patch.dict(os.environ, {'XDG_RUNTIME_DIR': runtime}):
            fifo = Path(runtime) / 'sway-osd.fifo'
            os.mkfifo(fifo, 0o600)
            # No reader must fail immediately, rather than hanging a keypress.
            with self.assertRaises(OSError):
                status.show_osd(50, 'volume')
            reader = os.open(fifo, os.O_RDONLY | os.O_NONBLOCK)
            try:
                for percent, style, expected in [(35, 'volume', b'35 volume\n'),
                                                 (110, 'brightness', b'100 brightness\n'),
                                                 (35, 'muted', b'35 muted\n')]:
                    status.show_osd(percent, style)
                    self.assertEqual(os.read(reader, 128), expected)
            finally:
                os.close(reader)

    def test_volume_cli_rejects_unknown_actions_and_reports_command_failure(self):
        for arguments, error, expected_code in [
                (['--volume', 'louder'], None, 2),
                (['--volume', 'up'], subprocess.CalledProcessError(1, 'wpctl'), 1),
                (['--volume', 'down'], subprocess.TimeoutExpired('wpctl', 3), 1),
                (['--volume', 'mute'], FileNotFoundError('wpctl'), 1)]:
            with self.subTest(arguments=arguments, error=error), \
                    patch.object(sys, 'argv', ['status.py', *arguments]), \
                    patch.object(status, 'run', side_effect=error) as run, \
                    patch.object(sys, 'stderr', io.StringIO()), \
                    self.assertRaises(SystemExit) as raised:
                status.main()
            self.assertEqual(raised.exception.code, expected_code)
            if expected_code == 2:
                run.assert_not_called()

    def test_hardware_shortcuts_do_not_import_dbus_libraries(self):
        # A fresh process catches imports performed before main(), too.
        code = '''
import importlib.util
import sys
spec = importlib.util.spec_from_file_location('status', sys.argv[1])
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
s.run = lambda *args: 'Volume: 0.35' if args[0] == 'wpctl' else 'backlight,backlight,35,35%,100'
s.show_osd = lambda *args: None
for option in ('--volume', '--brightness'):
    sys.argv = ['status.py', option, 'up']
    s.main()
    assert 'gi' not in sys.modules
'''
        subprocess.run([sys.executable, '-B', '-c', code, str(STATUS)],
                       capture_output=True, text=True, check=True, timeout=5)

    def test_keybindings_adjust_reported_sink_before_requesting_feedback(self):
        config = (STATUS.parent.parent / 'config.d/30-keybinds.conf').read_text()
        commands = {'RaiseVolume': f'set-volume -l 1.0 {status.DEFAULT_SINK} 5%+',
                    'LowerVolume': f'set-volume {status.DEFAULT_SINK} 5%-',
                    'Mute': f'set-mute {status.DEFAULT_SINK} toggle'}
        for key, command in commands.items():
            self.assertIn(f'bindsym XF86Audio{key} exec wpctl {command} '
                          "&& printf 'refresh volume\\n'", config)
        for key, step in [('Down', '5%-'), ('Up', '5%+')]:
            self.assertIn(f'bindsym XF86MonBrightness{key} exec brightnessctl set {step} '
                          "&& printf 'refresh brightness\\n'", config)

    def test_direct_shortcut_notifies_only_after_successful_adjustment(self):
        config = (STATUS.parent.parent / 'config.d/30-keybinds.conf').read_text()
        command = next(line.split(' exec ', 1)[1] for line in config.splitlines()
                       if line.startswith('bindsym XF86AudioRaiseVolume '))
        with tempfile.TemporaryDirectory() as runtime:
            fake = Path(runtime) / 'wpctl'
            fake.write_text('#!/bin/sh\nexit "${KEY_TEST_EXIT:-0}"\n')
            fake.chmod(0o755)
            fifo = Path(runtime) / 'sway-osd.fifo'
            env = {**os.environ, 'XDG_RUNTIME_DIR': runtime,
                   'PATH': runtime + ':' + os.environ['PATH'], 'KEY_TEST_EXIT': '3'}
            failure = subprocess.run(['/bin/sh', '-c', command], env=env, timeout=2)
            self.assertEqual(failure.returncode, 3)
            self.assertFalse(fifo.exists())
            env['KEY_TEST_EXIT'] = '0'
            subprocess.run(['/bin/sh', '-c', command], env=env, check=True, timeout=2)
            self.assertEqual(fifo.read_text(), 'refresh volume\n')

    def test_coffee_toggles_real_descriptor_lifetime_and_colour(self):
        inhibitor = status.IdleInhibitor()
        bus, descriptors = Mock(), Mock()
        reply = status.GLib.Variant('(h)', (0,))
        bus.call_with_unix_fd_list_sync.return_value = reply, descriptors
        descriptors.get.return_value = 123
        with patch.object(status.Gio, 'bus_get_sync', return_value=bus), \
                patch.object(status.os, 'close') as close:
            self.assertEqual(inhibitor.blocks()[0]['full_text'], '☕ OFF')
            inhibitor.toggle()
            call = bus.call_with_unix_fd_list_sync.call_args.args
            self.assertEqual(call[3], 'Inhibit')
            self.assertEqual(call[4].unpack(), ('idle', 'swaybar coffee',
                                               'Keep awake from swaybar', 'block'))
            descriptors.get.assert_called_once_with(0)
            self.assertEqual(inhibitor.blocks()[0]['full_text'], '☕ ON')
            self.assertEqual(inhibitor.blocks()[0]['color'], '#f5c2e7')
            inhibitor.toggle()
            close.assert_called_once_with(123)
            self.assertEqual(inhibitor.blocks()[0]['full_text'], '☕ OFF')
            inhibitor.toggle()
            inhibitor.close()
            inhibitor.close()
            self.assertEqual(close.call_count, 2)

    def test_failed_inhibition_stays_off(self):
        inhibitor = status.IdleInhibitor()
        with patch.object(status.Gio, 'bus_get_sync', side_effect=status.GLib.Error('denied')):
            with self.assertRaises(status.GLib.Error):
                inhibitor.toggle()
        self.assertEqual(inhibitor.blocks()[0]['full_text'], '☕ OFF')

    def test_click_stream_filters_buttons_and_recovers_from_bad_events(self):
        stream = '''[
{"name":"volume","button":1}
,{"name":"coffee","button":3}
invalid
,null
,{"name":"coffee","button":1}
,{"name":"coffee","button":1}
'''
        refresh = Mock()
        with patch.object(status, 'inhibitor') as inhibitor, \
                patch.object(sys, 'stdin', io.StringIO(stream)), \
                patch.object(sys, 'stderr', io.StringIO()) as errors:
            inhibitor.toggle.side_effect = [status.GLib.Error('denied'), None]
            status.read_clicks(refresh)
            self.assertEqual(inhibitor.toggle.call_count, 2)
            refresh.assert_called_once_with()
            self.assertIn('denied', errors.getvalue())

    def test_missing_or_malformed_volume_is_a_recoverable_error(self):
        for response in ('', 'Volume:', 'Volume: unknown', 'Volume: nan'):
            with self.subTest(response=response), patch.object(status, 'run', return_value=response):
                with self.assertRaises(ValueError):
                    status.volume()

    def test_missing_device_metadata_does_not_hide_current_volume(self):
        failures = [subprocess.TimeoutExpired('wpctl', 3),
                    subprocess.CalledProcessError(3, 'wpctl')]
        for failure in failures:
            for before_failure in ([], ['device.id = "102"']):
                responses = ['Volume: 0.65', *before_failure, failure]
                with self.subTest(responses=responses), patch.object(status, 'run', side_effect=responses):
                    self.assertEqual(status.volume()[0]['full_text'], ' 65')

    def test_muted_and_headset_readings(self):
        for text, expected in [('Volume: 0.60', ' 60'), ('Volume: 0.60 [MUTED]', ' MM')]:
            responses = [text, 'device.id = "102"', 'device.form-factor = "headset"']
            with self.subTest(text=text), patch.object(status, 'run', side_effect=responses):
                self.assertEqual(status.volume()[0]['full_text'], expected)

    def test_worker_survives_unexpected_exception_and_keeps_updating(self):
        # Run the real stream loop. A parser error previously killed its worker,
        # leaving a cached value displayed until Sway restarted the provider.
        code = '''
import importlib.util
import os
import signal
import sys
spec = importlib.util.spec_from_file_location('status', sys.argv[1])
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
calls = 0
def reading():
    global calls
    calls += 1
    if calls == 1:
        return [s.block('volume', '20')]
    if calls in (2, 3):
        raise IndexError('temporary bad response')
    if calls == 4:
        return [s.block('volume', '65')]
    os.kill(os.getpid(), signal.SIGTERM)
    return [s.block('volume', '65')]
s.MODULES = [('volume', reading, 0.04)]
sys.argv = [sys.argv[0]]
s.main()
'''
        result = subprocess.run([sys.executable, '-B', '-c', code, str(STATUS)],
                                capture_output=True, text=True, timeout=5, check=True)
        header, body = result.stdout.split('\n', 1)
        self.assertTrue(json.loads(header)['click_events'])
        frames = json.loads(body + ']')
        self.assertEqual(frames[0][0]['full_text'], '20')
        self.assertIn([], frames)
        self.assertEqual(frames[-1][0]['full_text'], '65')
        self.assertEqual(result.stderr.count('IndexError: temporary bad response'), 1)


if __name__ == '__main__':
    unittest.main()
