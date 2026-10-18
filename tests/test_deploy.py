"""Isolated temporary-home checks; never touch live settings."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('deploy', Path(__file__).resolve().parents[1] / 'scripts/deploy.py')
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.repo = root / 'repo'
        self.home = root / 'target'
        self.home.mkdir()
        (self.repo / 'home/.config/app').mkdir(parents=True)
        self.source = self.repo / 'home/.config/app/config'
        self.source.write_text('managed\n')
        self.dest = self.home / '.config/app/config'
        self.manifest(['.config/app/config'])
        self.output = io.StringIO()
        self.addCleanup(self.output.close)
        self.capture = contextlib.redirect_stdout(self.output)
        self.capture.__enter__()
        self.addCleanup(self.capture.__exit__, None, None, None)

    def manifest(self, paths):
        (self.repo / 'manifest.json').write_text(json.dumps({'version': 1, 'paths': paths}))

    def original(self, text='original\n'):
        self.dest.parent.mkdir(parents=True, exist_ok=True)
        self.dest.write_text(text)

    def test_dry_run_writes_nothing(self):
        deploy.deploy(self.repo, self.home)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_apply_keeps_unmanaged_and_rollback_restores_original(self):
        self.original()
        unmanaged = self.dest.parent / 'state.db'
        unmanaged.write_text('unmanaged')
        run = deploy.deploy(self.repo, self.home, True)
        self.assertTrue(self.dest.is_symlink())
        self.assertEqual(self.dest.read_text(), 'managed\n')
        self.assertEqual(run.stat().st_mode & 0o777, 0o700)
        self.assertEqual((run / 'journal.json').stat().st_mode & 0o777, 0o600)
        self.assertIsNone(deploy.deploy(self.repo, self.home, True))
        deploy.rollback(self.home, run.name)
        self.assertTrue(self.dest.is_symlink())
        deploy.rollback(self.home, run.name, True)
        self.assertFalse(self.dest.is_symlink())
        self.assertEqual(self.dest.read_text(), 'original\n')
        self.assertEqual(unmanaged.read_text(), 'unmanaged')
        deploy.rollback(self.home, run.name, True)
        self.assertEqual(self.dest.read_text(), 'original\n')

    def test_rollback_removes_only_owned_links(self):
        run = deploy.deploy(self.repo, self.home, True)
        self.dest.unlink()
        self.dest.write_text('new user file')
        with self.assertRaisesRegex(ValueError, 'rollback conflict'):
            deploy.rollback(self.home, run.name, True)
        self.assertEqual(self.dest.read_text(), 'new user file')

    def test_backup_restores_existing_symlink_without_following_it(self):
        outside = self.home / 'original'
        outside.write_text('outside')
        self.dest.parent.mkdir(parents=True)
        self.dest.symlink_to(outside)
        run = deploy.deploy(self.repo, self.home, True)
        deploy.rollback(self.home, run.name, True)
        self.assertEqual(os.readlink(self.dest), str(outside))
        self.assertEqual(outside.read_text(), 'outside')

    def test_new_file_rollback_and_idempotency(self):
        run = deploy.deploy(self.repo, self.home, True)
        deploy.rollback(self.home, run.name, True)
        self.assertFalse(deploy.exists(self.dest))
        deploy.rollback(self.home, run.name, True)
        self.assertFalse(deploy.exists(self.dest))

    def test_real_directory_destination_is_never_replaced(self):
        self.dest.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'real directory'):
            deploy.deploy(self.repo, self.home, True)
        self.assertFalse((self.home / '.local').exists())

    def test_unsafe_destination_parent_rejected_before_any_writes(self):
        other = Path(self.tmp.name) / 'outside'
        other.mkdir()
        (self.home / '.config').symlink_to(other, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'unsafe destination parent'):
            deploy.deploy(self.repo, self.home, True)
        self.assertEqual(list(other.iterdir()), [])

    def test_recovery_parent_symlink_rejected(self):
        other = Path(self.tmp.name) / 'outside'
        other.mkdir()
        (self.home / '.local').symlink_to(other, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'unsafe destination parent'):
            deploy.deploy(self.repo, self.home, True)
        self.assertFalse(self.dest.exists())

    def test_manifest_rejects_traversal_duplicates_and_overlap(self):
        for paths in (['../escape'], ['/etc/config'], ['.config/./app'],
                      ['.config/app/config', '.config/app/config'],
                      ['.config/app', '.config/app/config'], ['.local/state']):
            with self.subTest(paths=paths):
                self.manifest(paths)
                with self.assertRaises(ValueError):
                    deploy.deploy(self.repo, self.home, True)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_missing_source_preflight_does_not_partially_deploy(self):
        self.manifest(['.config/app/config', '.missing'])
        with self.assertRaisesRegex(ValueError, 'missing or dangling source'):
            deploy.deploy(self.repo, self.home, True)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_managed_symlink_and_dangling_dependencies(self):
        asset = self.repo / 'home/asset'
        asset.write_text('asset')
        self.source.unlink()
        self.source.symlink_to('../../asset')
        deploy.deploy(self.repo, self.home, True)
        self.assertEqual(self.dest.read_text(), 'asset')
        asset.unlink()
        with self.assertRaisesRegex(ValueError, 'missing or dangling source'):
            deploy.deploy(self.repo, self.home)

    def test_source_symlink_cannot_escape_to_arbitrary_file(self):
        self.source.unlink()
        self.source.symlink_to('/etc/passwd')
        with self.assertRaisesRegex(ValueError, 'escapes home subtree'):
            deploy.deploy(self.repo, self.home, True)

    def test_directory_asset_dangling_nested_symlink(self):
        assets = self.repo / 'home/assets'
        assets.mkdir()
        (assets / 'missing').symlink_to('absent')
        self.source.unlink()
        self.source.symlink_to('../../assets')
        with self.assertRaisesRegex(ValueError, 'dangling asset dependency'):
            deploy.deploy(self.repo, self.home, True)

    def test_bad_manifest_and_rollback_id(self):
        (self.repo / 'manifest.json').write_text('{"version":2,"paths":[]}')
        with self.assertRaisesRegex(ValueError, 'version 1'):
            deploy.deploy(self.repo, self.home)
        with self.assertRaises(ValueError):
            deploy.rollback(self.home, '../escape')

    def test_interrupted_apply_after_backup_is_recoverable(self):
        self.original()
        with patch.object(Path, 'symlink_to', side_effect=OSError('interrupted')):
            with self.assertRaises(OSError):
                deploy.deploy(self.repo, self.home, True)
        self.assertFalse(deploy.exists(self.dest))
        run = next((self.home / deploy.STATE).iterdir())
        deploy.rollback(self.home, run.name, True)
        self.assertEqual(self.dest.read_text(), 'original\n')

    def test_target_cannot_overwrite_source_checkout(self):
        with self.assertRaisesRegex(ValueError, 'inside the source checkout'):
            deploy.deploy(self.repo, self.repo / 'home', True)
        self.assertEqual(self.source.read_text(), 'managed\n')


if __name__ == '__main__':
    unittest.main()
