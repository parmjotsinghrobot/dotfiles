#!/usr/bin/env python3
"""Optional package and feature setup, used by deploy.py. Never sends mail."""
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

FEATURES = {
    'utilities': 'Install everyday utilities (btop, Thunar, pavucontrol, etc.)',
    'engineering': 'Install coursework tools (review packages/engineering-* first)',
    'emoji-typing': 'Install wtype for Wayland emoji typing',
    'bluetooth': 'Enable and start the system Bluetooth service',
    'network': 'Enable and start NetworkManager (may change network management)',
    'ui-fonts': 'Apply Iosevka UI fonts in this user session',
    'mail': 'Enable the existing daily-nonsense email timer for future logins',
}


def add_arguments(parser):
    parser.add_argument('--setup', action='store_true', help='ask about packages and optional features (still previews unless --apply)')
    parser.add_argument('--install-packages', choices=('official', 'all'), help='install desktop/appearance packages; all also includes foreign packages via an existing AUR helper')
    parser.add_argument('--aur-helper', choices=('paru', 'yay'), help='existing helper used with --install-packages all; build reviews stay interactive')
    parser.add_argument('--feature', action='append', choices=FEATURES, default=[], help='add a feature; repeat for several (omitting a feature never disables it)')


def ask(question, default=False):
    suffix = ' [Y/n] ' if default else ' [y/N] '
    while True:
        answer = input(question + suffix).strip().casefold()
        if not answer:
            return default
        if answer in ('y', 'yes', 'n', 'no'):
            return answer in ('y', 'yes')
        print('Enter y or n.')


def select(args):
    if args.setup:
        if not sys.stdin.isatty():
            raise ValueError('--setup needs a terminal; use --install-packages and --feature for noninteractive selection')
        if args.install_packages is None and ask('Install Arch desktop and appearance packages?', True):
            args.install_packages = 'official'
            helper = args.aur_helper or next((h for h in ('paru', 'yay') if shutil.which(h)), None)
            if helper and ask(f'Also install foreign/AUR packages using {helper}? Review build sources when prompted.', True):
                args.install_packages = 'all'
                args.aur_helper = helper
            elif not helper:
                print('No paru/yay found. Only official packages selected; install/review foreign packages separately.')
        for name, description in FEATURES.items():
            if name not in args.feature and ask(description + '?'):
                args.feature.append(name)
    if args.aur_helper and args.install_packages != 'all':
        raise ValueError('--aur-helper requires --install-packages all')
    if args.install_packages == 'all' and not args.aur_helper:
        raise ValueError('--install-packages all requires --aur-helper paru or yay')
    if set(args.feature) & {'utilities', 'engineering', 'emoji-typing'} and not args.install_packages:
        raise ValueError('package features need --install-packages official or all')
    return args


def read_packages(repo, group, kind):
    packages = []
    for line in (repo / 'packages' / f'{group}-{kind}.txt').read_text().splitlines():
        name = line.split('#', 1)[0].strip()
        if name:
            if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9@._+:-]*', name):
                raise ValueError(f'invalid package name: {name!r}')
            packages.append(name)
    return packages


def arch_based(path=Path('/etc/os-release')):
    values = {}
    for line in path.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            values[key] = value.strip().strip('"').strip("'")
    return 'arch' in (values.get('ID', '') + ' ' + values.get('ID_LIKE', '')).split()


def plan(repo, args):
    """Build argv lists without invoking package managers or services."""
    before, after = [], []
    if args.install_packages:
        groups = ['desktop', 'appearance']
        groups += [group for feature, group in (('utilities', 'optional'), ('engineering', 'engineering')) if feature in args.feature]
        official = [p for group in groups for p in read_packages(repo, group, 'official')]
        if 'emoji-typing' in args.feature:
            official.append('wtype')
        if 'bluetooth' in args.feature:
            official += ['bluez', 'bluez-utils']
        if args.install_packages == 'all':
            # Foreign packages may need a compiler/toolchain to build.
            official += ['base-devel']
        before.append(['sudo', 'pacman', '-Syu', '--needed', '--', *dict.fromkeys(official)])
        if args.install_packages == 'all':
            foreign = [p for group in groups for p in read_packages(repo, group, 'aur-local')]
            if foreign:
                before.append([args.aur_helper, '-S', '--needed', '--', *dict.fromkeys(foreign)])
        elif any(read_packages(repo, group, 'aur-local') for group in groups):
            print('REVIEW foreign packages in packages/*-aur-local.txt separately; official-only setup does not install them.')
    if set(args.feature) & {'bluetooth', 'network'}:
        for feature, unit in (('bluetooth', 'bluetooth.service'), ('network', 'NetworkManager.service')):
            if feature in args.feature:
                after.append(['sudo', 'systemctl', 'enable', '--now', unit])
    if 'ui-fonts' in args.feature:
        after.append([sys.executable, str(repo / 'scripts/apply-ui-fonts.py'), '--apply'])
    if 'mail' in args.feature:
        # Do not use --now: Persistent=true can send catch-up mail immediately.
        after += [['systemctl', '--user', 'daemon-reload'],
                  ['systemctl', '--user', 'enable', 'daily-nonsense.timer']]
        print('MAIL: enables future logins only; leaves the current timer state unchanged. No send command is run.')
    return before, after


def validate(repo, target, args, commands):
    if not args.apply:
        return
    if os.geteuid() == 0:
        raise ValueError('run setup as your normal user; only package/system-service commands use sudo')
    if target.resolve() != Path.home().resolve():
        raise ValueError('package/feature setup can only apply to the current home; --target-home previews remain safe')
    if args.install_packages and not arch_based():
        raise ValueError('package installation is supported only on Arch and Arch-based distributions')
    for command in commands:
        if not shutil.which(command[0]):
            raise ValueError(f'required command not found: {command[0]}')
    if args.install_packages and not shutil.which('pacman'):
        raise ValueError('required command not found: pacman')
    if 'mail' in args.feature:
        root = target / '.local/share/daily-nonsense'
        required = [root / name for name in ('daily_nonsense.py', 'settings.json', 'email_template.txt', 'memo_library.json', 'config.json', 'recipients.json')]
        required += [target / '.config/systemd/user' / name for name in ('daily-nonsense.service', 'daily-nonsense.timer')]
        if not all(path.is_file() for path in required):
            raise ValueError('mail needs the existing daily-nonsense installation, private account configuration, recipients and user units; restore/setup it first (docs/SETUP.md)')


def show(commands):
    for command in commands:
        print('RUN     ' + shlex.join(command))


def execute(commands):
    for command in commands:
        print('RUN     ' + shlex.join(command), flush=True)
        subprocess.run(command, check=True)
