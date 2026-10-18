#!/usr/bin/env python3
"""Retire narrowly identified stale startup files. Dry-run unless --apply."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import uuid

STATE = Path('.local/state/dotfiles/legacy-cleanup')
BROKEN_UNITS = {'mpd-notification.service', 'gamemoded.service', 'modprobed-db.service',
                'yams.service', 'spotblock.service'}
CAMERA = Path('/usr/lib/python3.14/site-packages/CameraCtrls/cameractrlsd.py')


def present(path):
    return os.path.lexists(path)


def safe_parents(home, relative):
    """Never traverse symlinked directories, including recovery storage."""
    parent = home
    for part in Path(relative).parts[:-1]:
        parent /= part
        if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
            raise ValueError(f'unsafe parent: {parent}')


def content(path):
    if path.is_symlink() or not path.is_file():
        return ''
    return path.read_text(errors='replace')


def candidates(home):
    found = []
    units = home / '.config/systemd/user'
    safe_parents(home, '.config/systemd/user/entry')
    if units.is_dir():
        for group in sorted(units.iterdir()):
            if not group.name.endswith('.wants') or group.is_symlink() or not group.is_dir():
                continue
            for name in sorted(BROKEN_UNITS):
                path = group / name
                if path.is_symlink() and not path.exists():
                    found.append((path.relative_to(home), 'broken enabled legacy unit link'))
    checks = [
        (Path('.config/systemd/user/firefox-profile@.service'),
         lambda text: bool(re.search(r'^ExecStart=%h/\.local/bin/firefox-sync\.sh(?:\s|$)', text, re.M))
         and not (home / '.local/bin/firefox-sync.sh').exists(), 'missing Firefox profile helper'),
        (Path('.config/systemd/user/cameractrlsd.service'),
         lambda text: f'ExecStart={CAMERA}' in text.splitlines() and not CAMERA.exists(),
         'missing exact Python 3.14 CameraCtrls entrypoint'),
        (Path('.config/autostart/lunarclient.desktop'),
         lambda text: bool(re.search(r'^Exec=/tmp/\.mount_[^\n]*$', text, re.M)),
         'temporary AppImage mount in autostart'),
        (Path('.local/bin/launch-waybar'),
         lambda text: 'CONFIG_FILES="$HOME/.config/waybar/config $HOME/.config/waybar/style.css"' in text
         and 'inotifywait -e create,modify $CONFIG_FILES' in text and 'killall waybar' in text
         and not (home / '.config/waybar/config').exists()
         and not (home / '.config/waybar/style.css').exists(), 'retired Waybar watcher with missing configuration'),
    ]
    for relative, matches, reason in checks:
        safe_parents(home, relative)
        text = content(home / relative)
        if text and matches(text):
            found.append((relative, reason))
    return found


def write_journal(run, journal):
    temp = run / 'journal.tmp'
    with open(temp, 'w', opener=lambda path, flags: os.open(path, flags, 0o600)) as stream:
        json.dump(journal, stream, indent=2)
        stream.write('\n')
    temp.replace(run / 'journal.json')


def cleanup(home, apply=False):
    home = Path(home).resolve()
    matches = candidates(home)
    for relative, reason in matches:
        print(f'{"RETIRE" if apply else "WOULD RETIRE"} {relative}: {reason}')
    if not matches or not apply:
        return None
    safe_parents(home, STATE / 'run/journal.json')
    state = home / STATE
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    run = state / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8])
    run.mkdir(mode=0o700)
    journal = {'version': 1, 'target_home': str(home), 'entries': []}
    write_journal(run, journal)
    for index, (relative, reason) in enumerate(matches):
        # Record intent before rename, so even an interrupted run is recoverable.
        safe_parents(home, relative)
        entry = {'path': str(relative), 'backup': str(index), 'reason': reason}
        journal['entries'].append(entry)
        write_journal(run, journal)
        (home / relative).rename(run / str(index))
    print(f'Backup: {run}\nRestore: python3 scripts/cleanup_legacy.py --target-home {str(home)!r} --rollback {run.name} --apply')
    return run


def rollback(home, run_id, apply=False):
    home = Path(home).resolve()
    if not re.fullmatch(r'\d{8}T\d{6}Z-[0-9a-f]{8}', run_id):
        raise ValueError('invalid backup run ID')
    relative_run = STATE / run_id
    safe_parents(home, relative_run / 'journal.json')
    run = home / relative_run
    journal_path = run / 'journal.json'
    if journal_path.is_symlink():
        raise ValueError('unsafe journal symlink')
    journal = json.loads(journal_path.read_text())
    if journal.get('version') != 1 or journal.get('target_home') != str(home):
        raise ValueError('journal target/version mismatch')
    entries = []
    for entry in journal['entries']:
        relative = Path(entry['path'])
        backup = entry['backup']
        if relative.is_absolute() or '..' in relative.parts or not relative.parts or not str(backup).isdigit():
            raise ValueError('unsafe journal entry')
        safe_parents(home, relative)
        dest, saved = home / relative, run / backup
        if not present(saved):
            continue  # Already restored, or interrupted before the move.
        if present(dest):
            raise ValueError(f'restore conflict: {dest}; move the new entry aside first')
        entries.append((dest, saved))
    for dest, saved in entries:
        print(f'{"RESTORE" if apply else "WOULD RESTORE"} {dest.relative_to(home)}')
        if apply:
            dest.parent.mkdir(parents=True, exist_ok=True)
            saved.rename(dest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-home', type=Path, default=Path.home())
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--rollback', metavar='RUN_ID')
    args = parser.parse_args()
    try:
        if args.rollback:
            rollback(args.target_home, args.rollback, args.apply)
        else:
            cleanup(args.target_home, args.apply)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f'cleanup: {error}\n')


if __name__ == '__main__':
    main()
