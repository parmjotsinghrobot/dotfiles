"""Protocol and lifecycle checks for the percentage overlay."""
import configparser
import importlib.util
import queue
from pathlib import Path
import unittest
from unittest.mock import Mock, patch


SOURCE = Path(__file__).resolve().parents[1] / 'home/.config/sway/swaybar/osd.py'
spec = importlib.util.spec_from_file_location('hardware_osd', SOURCE)
osd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(osd)


class HardwareOSDTests(unittest.TestCase):
    def overlay(self):
        overlay = osd.Overlay.__new__(osd.Overlay)
        config = configparser.ConfigParser()
        config.read(SOURCE.with_name('osd.ini'))
        overlay.settings = config['overlay']
        overlay.window, overlay.area = Mock(), Mock()
        overlay.timer, overlay.pending = None, b''
        overlay.refresh_requests = queue.SimpleQueue()
        overlay.fade_timer, overlay.opacity = None, 1.0
        overlay.percent, overlay.style = 0, 'volume'
        return overlay

    def test_protocol_accepts_percent_and_styles(self):
        for line, expected in [('0 volume', (0, 'volume')), ('100 brightness', (100, 'brightness')),
                               ('35 muted', (35, 'muted'))]:
            self.assertEqual(osd.parse_reading(line), expected)
        for line in ('', '-1 volume', '101 volume', '35 unknown', 'nan volume', '35 volume extra'):
            with self.subTest(line=line), self.assertRaises(ValueError):
                osd.parse_reading(line)

    def test_updates_replace_the_value_and_restart_hide_timer(self):
        overlay = self.overlay()
        with patch.object(osd.GLib, 'timeout_add', side_effect=[101, 102]) as timer, \
                patch.object(osd.GLib, 'source_remove') as remove:
            overlay.update('35 volume')
            overlay.update('60 brightness')
            self.assertEqual((overlay.percent, overlay.style), (60, 'brightness'))
            remove.assert_called_once_with(101)
            self.assertEqual(timer.call_args.args[0], 900)
            self.assertEqual(overlay.window.show_all.call_count, 2)
            self.assertEqual(overlay.area.queue_draw.call_count, 2)
            overlay.hide()
            overlay.window.hide.assert_called_once_with()
            self.assertIsNone(overlay.timer)

    def test_fade_progresses_then_hides_and_new_input_cancels_it(self):
        overlay = self.overlay()
        with patch.object(osd.GLib, 'get_monotonic_time',
                          side_effect=[1000000, 1090000, 1180000]), \
                patch.object(osd.GLib, 'timeout_add', return_value=201):
            self.assertFalse(overlay.begin_fade())
            self.assertTrue(overlay.fade_step())
            self.assertAlmostEqual(overlay.opacity, 0.5)
            overlay.window.hide.assert_not_called()
            self.assertFalse(overlay.fade_step())
            self.assertEqual(overlay.opacity, 0)
            overlay.window.hide.assert_called_once_with()
        overlay.fade_timer, overlay.opacity = 202, 0.3
        with patch.object(osd.GLib, 'source_remove') as remove, \
                patch.object(osd.GLib, 'timeout_add', return_value=203):
            overlay.update('40 volume')
            remove.assert_called_once_with(202)
            self.assertEqual(overlay.opacity, 1)
            self.assertIsNone(overlay.fade_timer)

    def test_zero_duration_hides_without_animation(self):
        overlay = self.overlay()
        overlay.settings['fade'] = '0'
        with patch.object(osd.GLib, 'timeout_add') as timer:
            self.assertFalse(overlay.begin_fade())
            timer.assert_not_called()
            overlay.window.hide.assert_called_once_with()

    def test_fifo_input_handles_partial_and_multiple_lines(self):
        overlay = self.overlay()
        overlay.update = Mock()
        with patch.object(osd.os, 'read', side_effect=[b'35 vol', b'ume\n60 brightness\n']):
            overlay.read_input(0, osd.GLib.IO_IN)
            overlay.update.assert_not_called()
            overlay.read_input(0, osd.GLib.IO_IN)
        self.assertEqual([call.args[0] for call in overlay.update.call_args_list],
                         ['35 volume', '60 brightness'])
        self.assertEqual(overlay.pending, b'')

    def test_colours_include_optional_alpha(self):
        self.assertEqual(osd.colour('ffffff'), (1, 1, 1, 1))
        self.assertEqual(osd.colour('#00000000'), (0, 0, 0, 0))
        with self.assertRaises(ValueError):
            osd.colour('bad')

    def test_refresh_requests_are_queued_without_reading_devices_on_ui_thread(self):
        overlay = self.overlay()
        overlay.update = Mock()
        with patch.object(osd.os, 'read', return_value=b'refresh volume\nrefresh brightness\n'):
            overlay.read_input(0, osd.GLib.IO_IN)
        overlay.update.assert_not_called()
        self.assertEqual(overlay.refresh_requests.get_nowait(), 'volume')
        self.assertEqual(overlay.refresh_requests.get_nowait(), 'brightness')

    def test_feedback_uses_actual_level_and_mute_state(self):
        controls = Mock()
        controls.read_volume.return_value = 35, True
        self.assertEqual(osd.feedback_reading('volume', controls), '35 muted')
        controls.read_volume.return_value = 65, False
        self.assertEqual(osd.feedback_reading('volume', controls), '65 volume')
        controls.read_brightness.return_value = 40
        self.assertEqual(osd.feedback_reading('brightness', controls), '40 brightness')

    def test_refresh_worker_coalesces_queued_queries_and_updates_via_main_loop(self):
        overlay, controls = Mock(), Mock()
        overlay.refresh_requests.get.side_effect = ['volume', StopIteration]
        overlay.refresh_requests.get_nowait.side_effect = ['brightness', queue.Empty]
        controls.read_brightness.return_value = 40
        with patch.object(osd.GLib, 'idle_add') as idle, self.assertRaises(StopIteration):
            osd.refresh_worker(overlay, controls)
        controls.read_volume.assert_not_called()
        controls.read_brightness.assert_called_once_with()
        idle.assert_called_once_with(overlay.update, '40 brightness')


if __name__ == '__main__':
    unittest.main()
