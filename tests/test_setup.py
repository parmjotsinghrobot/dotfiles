"""Package/feature setup contract; all external mutations are mocked."""
import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

setup = load('setup_test', ROOT / 'scripts/setup.py')
deploy = load('setup_deploy_test', ROOT / 'scripts/deploy.py')


def arguments(*argv):
    parser = argparse.ArgumentParser()
    setup.add_arguments(parser)
    args = parser.parse_args(argv)
    args.apply = False
    return args


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.capture = contextlib.redirect_stdout(io.StringIO())
        self.capture.__enter__()
        self.addCleanup(self.capture.__exit__, None, None, None)

    def test_official_packages_deduplicate_and_include_selected_groups(self):
        args = setup.select(arguments('--install-packages', 'official', '--feature', 'utilities', '--feature', 'engineering', '--feature', 'emoji-typing'))
        before, after = setup.plan(ROOT, args)
        command, = before
        self.assertEqual(command[:6], ['sudo', 'pacman', '-Syu', '--needed', '--', 'alsa-utils'])
        self.assertEqual(command.count('gcc'), 1)
        self.assertIn('thunar', command)
        self.assertIn('typst', command)
        self.assertIn('wtype', command)
        self.assertNotIn('matlab-mpm', command)
        self.assertFalse(after)

    def test_foreign_packages_use_selected_helper_as_user(self):
        args = setup.select(arguments('--install-packages', 'all', '--aur-helper', 'yay', '--feature', 'engineering'))
        before, _ = setup.plan(ROOT, args)
        self.assertIn('base-devel', before[0])
        self.assertEqual(before[1][:4], ['yay', '-S', '--needed', '--'])
        self.assertIn('swayfx', before[1])
        self.assertIn('matlab-mpm', before[1])
        self.assertNotIn('--noconfirm', sum(before, []))

    def test_invalid_selections_fail(self):
        for argv in (('--install-packages', 'all'), ('--aur-helper', 'paru'), ('--feature', 'engineering')):
            with self.subTest(argv=argv), self.assertRaises(ValueError):
                setup.select(arguments(*argv))

    def test_mail_never_starts_or_sends(self):
        before, after = setup.plan(ROOT, arguments('--feature', 'mail', '--feature', 'mail'))
        self.assertFalse(before)
        self.assertEqual(after, [['systemctl', '--user', 'daemon-reload'], ['systemctl', '--user', 'enable', 'daily-nonsense.timer']])

    def test_declined_wizard_features_do_not_disable_anything(self):
        with patch.object(sys.stdin, 'isatty', return_value=True), patch('builtins.input', return_value='n'):
            args = setup.select(arguments('--setup'))
        self.assertIsNone(args.install_packages)
        self.assertFalse(args.feature)
        self.assertEqual(setup.plan(ROOT, args), ([], []))

    def test_wizard_selects_existing_helper_and_features(self):
        replies = ['y', 'y'] + ['y'] * len(setup.FEATURES)
        with patch.object(sys.stdin, 'isatty', return_value=True), patch('builtins.input', side_effect=replies), patch.object(setup.shutil, 'which', return_value='/usr/bin/paru'):
            args = setup.select(arguments('--setup'))
        self.assertEqual(args.install_packages, 'all')
        self.assertEqual(args.aur_helper, 'paru')
        self.assertEqual(set(args.feature), set(setup.FEATURES))

    def test_wizard_requires_terminal(self):
        with patch.object(sys.stdin, 'isatty', return_value=False), self.assertRaisesRegex(ValueError, 'terminal'):
            setup.select(arguments('--setup'))

    def test_arch_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'os-release'
            for contents, expected in (('ID=arch\n', True), ('ID=derivative\nID_LIKE="arch linux"\n', True), ('ID=debian\n', False), ('ID=archish\n', False)):
                path.write_text(contents)
                self.assertEqual(setup.arch_based(path), expected)

    def test_apply_refuses_root_other_homes_unsupported_os_and_missing_helper(self):
        args = arguments('--install-packages', 'all', '--aur-helper', 'paru')
        args.apply = True
        commands = setup.plan(ROOT, args)[0]
        with patch.object(setup.os, 'geteuid', return_value=0), self.assertRaisesRegex(ValueError, 'normal user'):
            setup.validate(ROOT, Path.home(), args, commands)
        with patch.object(setup.os, 'geteuid', return_value=1000):
            with self.assertRaisesRegex(ValueError, 'current home'):
                setup.validate(ROOT, Path('/tmp/other-home'), args, commands)
            with patch.object(setup, 'arch_based', return_value=False), self.assertRaisesRegex(ValueError, 'Arch-based'):
                setup.validate(ROOT, Path.home(), args, commands)
            with patch.object(setup, 'arch_based', return_value=True), patch.object(setup.shutil, 'which', side_effect=lambda name: None if name == 'paru' else '/usr/bin/' + name), self.assertRaisesRegex(ValueError, 'paru'):
                setup.validate(ROOT, Path.home(), args, commands)

    def test_mail_apply_requires_private_install_without_reading_secrets(self):
        args = arguments('--feature', 'mail')
        args.apply = True
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            with patch.object(setup.os, 'geteuid', return_value=1000), patch.object(setup.Path, 'home', return_value=home), patch.object(setup.shutil, 'which', return_value='/usr/bin/systemctl'):
                with self.assertRaisesRegex(ValueError, 'restore/setup'):
                    setup.validate(ROOT, home, args, [])
                root = home / '.local/share/daily-nonsense'
                units = home / '.config/systemd/user'
                root.mkdir(parents=True)
                units.mkdir(parents=True)
                for name in ('daily_nonsense.py', 'settings.json', 'email_template.txt', 'memo_library.json', 'config.json', 'recipients.json'):
                    (root / name).write_text('private data not parsed')
                for name in ('daily-nonsense.service', 'daily-nonsense.timer'):
                    (units / name).write_text('local units')
                setup.validate(ROOT, home, args, [])

    def test_execute_stops_on_first_failure(self):
        commands = [['sudo', 'pacman'], ['paru'], ['systemctl']]
        with patch.object(setup.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, commands[0])) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                setup.execute(commands)
        run.assert_called_once_with(commands[0], check=True)

    def test_package_list_rejects_arguments_and_shell_syntax(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'packages').mkdir()
            path = root / 'packages/desktop-official.txt'
            for name in ('--noconfirm', 'foo bar', '$(touch bad)'):
                path.write_text(name)
                with self.assertRaises(ValueError):
                    setup.read_packages(root, 'desktop', 'official')

    def test_external_asset_deferral_never_allows_missing_repo_source_or_apply(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo, home = root / 'repo', root / 'target'
            (repo / 'home').mkdir(parents=True)
            home.mkdir()
            (repo / 'manifest.json').write_text(json.dumps({'version': 1, 'paths': ['theme']}))
            source = repo / 'home/theme'
            source.symlink_to('/usr/share/themes/dotfiles-test-nonexistent/gtk.css')
            deploy.deploy(repo, home, pending_assets=True)
            self.assertFalse(list(home.iterdir()))
            with self.assertRaises(ValueError):
                deploy.deploy(repo, home, apply=True, pending_assets=True)
            with self.assertRaises(ValueError):
                deploy.deploy(repo, home, apply=True)
            source.unlink()
            with self.assertRaises(ValueError):
                deploy.deploy(repo, home, pending_assets=True)
            source.symlink_to('theme')
            with self.assertRaises(ValueError):
                deploy.deploy(repo, home, pending_assets=True)

    def run_main(self, argv, repo, module):
        with patch.object(deploy, 'REPO', repo), patch.object(sys, 'argv', ['deploy.py', *argv]), patch.object(importlib.util, 'module_from_spec', return_value=module), patch.object(importlib.machinery.SourceFileLoader, 'exec_module'):
            return deploy.main()

    def test_main_preview_has_no_external_commands_or_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'home'
            target.mkdir()
            with patch.object(setup.subprocess, 'run', side_effect=AssertionError('preview invoked subprocess')):
                status = self.run_main(['--install-packages', 'all', '--aur-helper', 'paru', '--feature', 'mail', '--target-home', str(target)], ROOT, setup)
            self.assertEqual(status, 0)
            self.assertFalse(list(target.iterdir()))

    def test_main_failed_packages_prevent_deployment_and_features(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'home'
            target.mkdir()
            with patch.object(setup, 'validate'), patch.object(setup, 'execute', side_effect=subprocess.CalledProcessError(1, ['pacman'])) as execute, patch.object(deploy, 'deploy') as link:
                status = self.run_main(['--install-packages', 'official', '--feature', 'mail', '--apply', '--target-home', str(target)], ROOT, setup)
            self.assertEqual(status, 1)
            execute.assert_called_once()
            link.assert_not_called()

    def test_main_orders_packages_links_features(self):
        events = []
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'home'
            target.mkdir()
            def execute(commands):
                events.append(commands[0][1])
            with patch.object(setup, 'validate'), patch.object(setup, 'execute', side_effect=execute), patch.object(deploy, 'deploy', side_effect=lambda *args: events.append('links')):
                status = self.run_main(['--install-packages', 'official', '--feature', 'mail', '--apply', '--target-home', str(target)], ROOT, setup)
            self.assertEqual(status, 0)
            self.assertEqual(events, ['pacman', 'links', '--user'])

    def test_main_conflicting_destination_stops_before_packages(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'home'
            (target / '.zshenv').mkdir(parents=True)
            with patch.object(setup, 'validate'), patch.object(setup, 'execute') as execute:
                status = self.run_main(['--install-packages', 'official', '--apply', '--target-home', str(target)], ROOT, setup)
            self.assertEqual(status, 1)
            execute.assert_not_called()

    def test_rollback_rejects_setup_flags(self):
        status = self.run_main(['--rollback', 'test-run', '--feature', 'mail'], ROOT, setup)
        self.assertEqual(status, 1)


if __name__ == '__main__':
    unittest.main()
