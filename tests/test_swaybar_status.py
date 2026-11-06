"""Focused checks for status recovery, volume commands and the coffee toggle."""
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch


STATUS = Path(__file__).resolve().parents[1] / 'home/.config/sway/swaybar/status.py'
SPEC = importlib.util.spec_from_file_location('swaybar_status', STATUS)
status = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(status)


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
                    patch.object(status.threading, 'Thread') as thread:
                status.main()
                adjust.assert_called_once_with(action)
                thread.assert_not_called()

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

    def test_keybindings_dispatch_to_shared_volume_handler(self):
        config = (STATUS.parent.parent / 'config.d/30-keybinds.conf').read_text()
        for key, action in [('RaiseVolume', 'up'), ('LowerVolume', 'down'), ('Mute', 'mute')]:
            self.assertIn(f'bindsym XF86Audio{key} exec python3 '
                          f'~/.config/sway/swaybar/status.py --volume {action}', config)

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
