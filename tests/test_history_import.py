"""Exercise display-name mapping and idempotent native-cache merges."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('history_import', ROOT / 'scripts/import-tofi-history.py')
history = importlib.util.module_from_spec(spec)
spec.loader.exec_module(history)


class HistoryImportTests(unittest.TestCase):
    def test_native_formats_and_preserving_existing_fuzzel_usage(self):
        source = history.tofi_counts('100 Firefox\n80 Zed\n')
        existing = history.fuzzel_counts('firefox.desktop|3\nother.desktop|7\n')
        merged, imported, additions, unmatched, ambiguous = history.plan(
            source, existing, {'Firefox': {'firefox.desktop'}, 'Zed': {'dev.zed.Zed.desktop'}}, {})
        self.assertEqual(merged, {'firefox.desktop': 103, 'dev.zed.Zed.desktop': 80, 'other.desktop': 7})
        self.assertEqual(sum(additions.values()), 180)
        self.assertFalse(unmatched or ambiguous)
        # New Fuzzel launches survive another import; old Tofi counts aren't added twice.
        merged['firefox.desktop'] += 2
        again = history.plan(source, merged, {'Firefox': {'firefox.desktop'}, 'Zed': {'dev.zed.Zed.desktop'}}, imported)
        self.assertEqual(again[0]['firefox.desktop'], 105)
        self.assertFalse(again[2])

    def test_new_tofi_usage_adds_only_delta(self):
        merged, _, additions, _, _ = history.plan(
            {'Zed': 83}, {'zed.desktop': 90}, {'Zed': {'zed.desktop'}}, {'zed.desktop': 80})
        self.assertEqual(merged['zed.desktop'], 93)
        self.assertEqual(additions['zed.desktop'], 3)

    def test_unknown_and_ambiguous_names_are_not_guessed(self):
        merged, _, additions, unmatched, ambiguous = history.plan(
            {'Old app': 100, 'Duplicate': 50}, {'existing.desktop': 4},
            {'Duplicate': {'a.desktop', 'b.desktop'}}, {})
        self.assertEqual(merged, {'existing.desktop': 4})
        self.assertFalse(additions)
        self.assertIn('Old app', unmatched)
        self.assertEqual(ambiguous['Duplicate'], ['a.desktop', 'b.desktop'])

    def test_desktop_precedence_hidden_and_localized_names(self):
        with tempfile.TemporaryDirectory() as directory:
            user, system = Path(directory)/'user', Path(directory)/'system'
            for root in [user, system]:
                (root/'applications').mkdir(parents=True)
            (system/'applications/app.desktop').write_text('[Desktop Entry]\nType=Application\nName=Visible app\n')
            (user/'applications/app.desktop').write_text('[Desktop Entry]\nType=Application\nName=Hidden override\nHidden=true\n')
            (system/'applications/zed.desktop').write_text('[Desktop Entry]\nType=Application\nName=Zed\nName[fr]=Zed localized\n')
            (system/'applications/tool.desktop').write_text('[Desktop Entry]\nType=Application\nName=Hidden tool\nNoDisplay=true\n')
            names = history.desktop_names([user, system])
            self.assertNotIn('Visible app', names)
            self.assertNotIn('Hidden override', names)
            self.assertNotIn('Hidden tool', names)
            self.assertEqual(names['Zed'], {'zed.desktop'})
            self.assertEqual(names['Zed localized'], {'zed.desktop'})

    def test_unknown_cache_format_is_rejected(self):
        with self.assertRaises(ValueError):
            history.fuzzel_counts('unrecognized native cache format\n')
